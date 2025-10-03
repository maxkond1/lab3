import os
import xml.etree.ElementTree as ET
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import TouristRoute

XML_FILE_PATH = os.path.join('media', 'tourist_routes.xml')

def ensure_xml_file_exists():
    """Создает базовую структуру XML файла"""
    if not os.path.exists(XML_FILE_PATH):
        os.makedirs(os.path.dirname(XML_FILE_PATH), exist_ok=True)
        
        root = ET.Element('tourist_routes')
        root.set('version', '1.0')
        root.set('created', datetime.now().isoformat())
        tree = ET.ElementTree(root)
        tree.write(XML_FILE_PATH, encoding='utf-8', xml_declaration=True)

def get_model_fields():
    """Автоматически получает все поля модели кроме служебных"""
    exclude_fields = ['id', 'created_at']
    fields = []
    
    for field in TouristRoute._meta.fields:
        if field.name not in exclude_fields:
            fields.append({
                'name': field.name,
                'verbose_name': field.verbose_name,
                'type': type(field).__name__,
                'required': not field.blank,
                'choices': getattr(field, 'choices', None),
                'max_length': getattr(field, 'max_length', None),
            })
    
    return fields

def auto_extract_form_data(request_post):
    """Автоматически извлекает данные формы"""
    fields = get_model_fields()
    data = {}
    
    for field in fields:
        field_name = field['name']
        if field_name in request_post:
            data[field_name] = request_post[field_name].strip()
        else:
            data[field_name] = ''
    
    return data

def auto_validate_route_data(data):
    """Автоматическая валидация на основе полей модели"""
    fields = get_model_fields()
    errors = []
    
    for field in fields:
        value = data.get(field['name'], '')
        
        # Проверка обязательных полей
        if field['required'] and (not value or str(value).strip() == ''):
            errors.append(f"Поле '{field['verbose_name']}' обязательно для заполнения")
        
        # Проверка числовых полей
        if value and field['type'] in ['DecimalField']:
            try:
                float_value = float(value)
                if float_value <= 0:
                    errors.append(f"Поле '{field['verbose_name']}' должно быть положительным числом")
            except (ValueError, TypeError):
                errors.append(f"Поле '{field['verbose_name']}' должно быть числом")
        
        elif value and field['type'] in ['PositiveIntegerField', 'IntegerField']:
            try:
                int_value = int(value)
                if int_value <= 0:
                    errors.append(f"Поле '{field['verbose_name']}' должно быть положительным числом")
            except (ValueError, TypeError):
                errors.append(f"Поле '{field['verbose_name']}' должно быть целым числом")
    
    return errors

def auto_create_route(data):
    """Автоматическое создание объекта маршрута"""
    fields = get_model_fields()
    route_data = {}
    
    for field in fields:
        field_name = field['name']
        value = data.get(field_name, '')
        
        if value:
            # Преобразование типов
            if field['type'] in ['DecimalField']:
                route_data[field_name] = float(value)
            elif field['type'] in ['PositiveIntegerField', 'IntegerField']:
                route_data[field_name] = int(value)
            else:
                route_data[field_name] = value
    
    return TouristRoute(**route_data)

def save_routes_to_xml():
    """Автоматическое сохранение всех маршрутов в XML"""
    ensure_xml_file_exists()
    
    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        
        # Удаляем старые маршруты
        for route_elem in root.findall('route'):
            root.remove(route_elem)
        
        # Добавляем текущие маршруты
        routes = TouristRoute.objects.all().order_by('created_at')
        for route in routes:
            route_elem = ET.SubElement(root, 'route')
            
            # Автоматически добавляем все поля
            fields = get_model_fields()
            for field in fields:
                field_name = field['name']
                value = getattr(route, field_name)
                if value is not None:
                    ET.SubElement(route_elem, field_name).text = str(value)
            
            # Добавляем created_at отдельно
            ET.SubElement(route_elem, 'created_at').text = route.created_at.isoformat()
        
        root.set('last_updated', datetime.now().isoformat())
        tree.write(XML_FILE_PATH, encoding='utf-8', xml_declaration=True)
        
    except ET.ParseError:
        ensure_xml_file_exists()
        save_routes_to_xml()

def load_routes_from_xml():
    """Автоматическая загрузка маршрутов из XML"""
    ensure_xml_file_exists()
    
    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        
        # Очищаем текущие данные
        TouristRoute.objects.all().delete()
        
        # Загружаем маршруты из XML
        for route_elem in root.findall('route'):
            route_data = {}
            fields = get_model_fields()
            
            for field in fields:
                field_name = field['name']
                elem = route_elem.find(field_name)
                if elem is not None and elem.text:
                    route_data[field_name] = elem.text
            
            # Создаем маршрут если есть обязательные поля
            required_fields = [field['name'] for field in fields if field['required']]
            if all(field in route_data for field in required_fields):
                try:
                    route = auto_create_route(route_data)
                    route.save()
                except (ValueError, TypeError) as e:
                    print(f"Ошибка создания маршрута: {e}")
                    continue
                    
    except ET.ParseError:
        ensure_xml_file_exists()

def index(request):
    return render(request, 'routes_app/index.html')

def add_route(request):
    if request.method == 'POST':
        # Автоматически извлекаем данные
        route_data = auto_extract_form_data(request.POST)
        
        # Автоматически валидируем
        errors = auto_validate_route_data(route_data)
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'routes_app/add_route.html', {
                'form_data': route_data,
                'model_fields': get_model_fields()
            })
        
        try:
            # Автоматически создаем и сохраняем
            route = auto_create_route(route_data)
            route.save()
            
            # Автоматически обновляем XML
            save_routes_to_xml()
            
            messages.success(request, f'Маршрут "{route.name}" успешно сохранен!')
            return redirect('routes_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при сохранении: {str(e)}')
            return render(request, 'routes_app/add_route.html', {
                'form_data': route_data,
                'model_fields': get_model_fields()
            })
    
    return render(request, 'routes_app/add_route.html', {
        'model_fields': get_model_fields()
    })

def upload_xml(request):
    if request.method == 'POST' and request.FILES.get('xml_file'):
        uploaded_file = request.FILES['xml_file']
        
        if not uploaded_file.name.endswith('.xml'):
            messages.error(request, "Поддерживаются только XML файлы")
            return redirect('upload_xml')
        
        try:
            file_content = uploaded_file.read().decode('utf-8')
            
            # Проверяем что это валидный XML
            ET.fromstring(file_content)
            
            # Сохраняем новый файл
            with open(XML_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Загружаем данные из XML
            load_routes_from_xml()
            
            messages.success(request, 'XML файл успешно загружен!')
            return redirect('routes_list')
                
        except ET.ParseError as e:
            messages.error(request, f'Ошибка в XML файле: {str(e)}')
        except Exception as e:
            messages.error(request, f'Ошибка загрузки: {str(e)}')
    
    return render(request, 'routes_app/upload_xml.html')

def routes_list(request):
    # Загружаем актуальные данные
    load_routes_from_xml()
    
    routes = TouristRoute.objects.all().order_by('-created_at')
    
    # Читаем XML содержимое
    xml_content = None
    if os.path.exists(XML_FILE_PATH):
        try:
            with open(XML_FILE_PATH, 'r', encoding='utf-8') as f:
                xml_content = f.read()
        except:
            xml_content = "Ошибка чтения файла"
    
    context = {
        'routes': routes,
        'xml_content': xml_content,
        'xml_file_exists': os.path.exists(XML_FILE_PATH),
    }
    
    return render(request, 'routes_app/routes_list.html', context)

def delete_route(request, route_id):
    try:
        route = TouristRoute.objects.get(id=route_id)
        route_name = route.name
        route.delete()
        save_routes_to_xml()
        messages.success(request, f'Маршрут "{route_name}" удален!')
    except TouristRoute.DoesNotExist:
        messages.error(request, 'Маршрут не найден')
    
    return redirect('routes_list')

def download_xml(request):
    if not os.path.exists(XML_FILE_PATH):
        messages.error(request, 'XML файл не существует')
        return redirect('routes_list')
    
    from django.http import FileResponse
    response = FileResponse(open(XML_FILE_PATH, 'rb'))
    response['Content-Type'] = 'application/xml'
    response['Content-Disposition'] = f'attachment; filename="tourist_routes_{datetime.now().strftime("%Y%m%d")}.xml"'
    return response