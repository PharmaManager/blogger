from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
import xml.etree.ElementTree as ET
from django.conf import settings
import os
from datetime import datetime
import html
import re

def clean_html(html_content):
    """Nettoie le HTML pour le rendre compatible avec Blogger."""
    cleaned = html.escape(html_content)
    cleaned = re.sub(r'<img([^>]+)>', r'<img\1 />', cleaned)
    return cleaned

def convert_wp_to_blogger(input_file_path, output_file_path):
    tree = ET.parse(input_file_path)
    root = tree.getroot()
    
    ns = {'atom': 'http://www.w3.org/2005/Atom', 'app': 'http://www.w3.org/2007/app'}
    feed = ET.Element('{http://www.w3.org/2005/Atom}feed')
    
    title = ET.SubElement(feed, 'title')
    title.text = 'Blog WordPress Importé'
    updated = ET.SubElement(feed, 'updated')
    updated.text = datetime.now().isoformat() + 'Z'
    
    for item in root.findall('.//item'):
        if item.find('wp:post_type', namespaces={'wp': 'http://wordpress.org/export/1.2/'}).text != 'post':
            continue
        
        entry = ET.SubElement(feed, '{http://www.w3.org/2005/Atom}entry')
        entry_title = ET.SubElement(entry, 'title')
        entry_title.text = item.find('title').text
        
        content = ET.SubElement(entry, 'content', {'type': 'html'})
        post_content = item.find('content:encoded', namespaces={'content': 'http://purl.org/rss/1.0/modules/content/'}).text or ""
        post_content = clean_html(post_content)
        content.text = post_content
        
        pub_date = item.find('wp:post_date', namespaces={'wp': 'http://wordpress.org/export/1.2/'}).text
        published = ET.SubElement(entry, 'published')
        published.text = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S').isoformat() + 'Z'
        
        author = ET.SubElement(entry, 'author')
        name = ET.SubElement(author, 'name')
        name.text = item.find('dc:creator', namespaces={'dc': 'http://purl.org/dc/elements/1.1/'}).text
        
        for category in item.findall('category'):
            ET.SubElement(entry, 'category', {'term': category.text, 'scheme': 'http://www.blogger.com/atom/ns#'})
        
        status = item.find('wp:status', namespaces={'wp': 'http://wordpress.org/export/1.2/'}).text
        if status != 'publish':
            control = ET.SubElement(entry, '{http://www.w3.org/2007/app}control')
            draft = ET.SubElement(control, '{http://www.w3.org/2007/app}draft')
            draft.text = 'yes'
    
    tree = ET.ElementTree(feed)
    tree.write(output_file_path, encoding='utf-8', xml_declaration=True)

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            # Sauvegarde temporaire du fichier WordPress
            temp_input_path = os.path.join(settings.MEDIA_ROOT, 'temp_wp_export.xml')
            with open(temp_input_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Conversion
            output_filename = "blogger_export.xml"
            output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
            convert_wp_to_blogger(temp_input_path, output_path)
            
            # Téléchargement automatique
            with open(output_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/xml')
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
                return response
    else:
        form = UploadFileForm()
    return render(request, 'converter/upload.html', {'form': form})
