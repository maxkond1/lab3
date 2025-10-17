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
    """Автоматическое создание объекта маршрута с обработкой отсутствующих полей"""
    fields = get_model_fields()
    route_data = {}
    
    for field in fields:
        field_name = field['name']
        value = data.get(field_name, '')
        
        if value:
            try:
                # Преобразование типов
                if field['type'] in ['DecimalField']:
                    route_data[field_name] = float(value)
                elif field['type'] in ['PositiveIntegerField', 'IntegerField']:
                    route_data[field_name] = int(value)
                else:
                    route_data[field_name] = value
            except (ValueError, TypeError):
                # Если преобразование не удалось, используем значения по умолчанию
                if field['type'] in ['DecimalField']:
                    route_data[field_name] = 0.0
                elif field['type'] in ['PositiveIntegerField', 'IntegerField']:
                    route_data[field_name] = 0
                else:
                    route_data[field_name] = ''
        else:
            # Устанавливаем значения по умолчанию для пустых полей
            if field['type'] in ['DecimalField']:
                route_data[field_name] = 0.0
            elif field['type'] in ['PositiveIntegerField', 'IntegerField']:
                route_data[field_name] = 0
            else:
                route_data[field_name] = ''
    
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
    """Автоматическая загрузка маршрутов из XML с строгой проверкой полей"""
    ensure_xml_file_exists()
    
    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        
        # Очищаем текущие данные
        TouristRoute.objects.all().delete()
        
        # Получаем информацию о полях модели
        model_fields = get_model_fields()
        required_fields = [field['name'] for field in model_fields if field['required']]
        
        loaded_count = 0
        error_messages = []
        
        # Загружаем маршруты из XML
        for i, route_elem in enumerate(root.findall('route'), 1):
            route_data = {}
            missing_required_fields = []
            invalid_fields = []
            
            # Проверяем наличие и валидность обязательных полей в XML
            for field_name in required_fields:
                elem = route_elem.find(field_name)
                if elem is None:
                    missing_required_fields.append(field_name)
                elif not elem.text or not elem.text.strip():
                    missing_required_fields.append(field_name)
                else:
                    # Проверяем валидность данных
                    value = elem.text.strip()
                    field_config = next((f for f in model_fields if f['name'] == field_name), None)
                    
                    if field_config:
                        if field_config['type'] in ['DecimalField']:
                            try:
                                float(value)
                            except (ValueError, TypeError):
                                invalid_fields.append(f"{field_name} (должно быть числом)")
                        elif field_config['type'] in ['PositiveIntegerField', 'IntegerField']:
                            try:
                                int(value)
                                if int(value) <= 0:
                                    invalid_fields.append(f"{field_name} (должно быть положительным числом)")
                            except (ValueError, TypeError):
                                invalid_fields.append(f"{field_name} (должно быть целым числом)")
                    
                    route_data[field_name] = value
            
            # Если отсутствуют обязательные поля или есть невалидные данные - ошибка
            if missing_required_fields:
                error_messages.append(f"Маршрут #{i}: отсутствуют обязательные поля: {', '.join(missing_required_fields)}")
                continue
            
            if invalid_fields:
                error_messages.append(f"Маршрут #{i}: невалидные данные в полях: {', '.join(invalid_fields)}")
                continue
            
            # Загружаем необязательные поля если они есть в XML
            for field in model_fields:
                field_name = field['name']
                if field_name not in route_data:  # Если поле еще не загружено (необязательное)
                    elem = route_elem.find(field_name)
                    if elem is not None and elem.text is not None:
                        value = elem.text.strip()
                        # Проверяем валидность необязательных полей
                        if value:
                            if field['type'] in ['DecimalField']:
                                try:
                                    float(value)
                                    route_data[field_name] = value
                                except (ValueError, TypeError):
                                    error_messages.append(f"Маршрут #{i}: поле '{field_name}' должно быть числом")
                                    continue
                            elif field['type'] in ['PositiveIntegerField', 'IntegerField']:
                                try:
                                    int_value = int(value)
                                    if int_value < 0:
                                        error_messages.append(f"Маршрут #{i}: поле '{field_name}' не может быть отрицательным")
                                        continue
                                    route_data[field_name] = value
                                except (ValueError, TypeError):
                                    error_messages.append(f"Маршрут #{i}: поле '{field_name}' должно быть целым числом")
                                    continue
                            else:
                                route_data[field_name] = value
                    else:
                        # Устанавливаем значения по умолчанию для отсутствующих необязательных полей
                        if field['type'] in ['DecimalField']:
                            route_data[field_name] = '0'
                        elif field['type'] in ['PositiveIntegerField', 'IntegerField']:
                            route_data[field_name] = '0'
                        else:
                            route_data[field_name] = ''
            
            try:
                # Создаем маршрут
                route = auto_create_route(route_data)
                route.save()
                loaded_count += 1
                
            except (ValueError, TypeError) as e:
                error_messages.append(f"Маршрут #{i}: ошибка создания - {str(e)}")
                continue
        
        # Если есть ошибки - выбрасываем исключение
        if error_messages:
            raise ValueError(f"Ошибки загрузки:\n" + "\n".join(error_messages))
        
        print(f"Успешно загружено: {loaded_count} маршрутов")
        return loaded_count
                    
    except ET.ParseError as e:
        print(f"Ошибка парсинга XML: {e}")
        ensure_xml_file_exists()
        raise

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
            
            # Пробуем распарсить XML
            try:
                tree = ET.fromstring(file_content)
            except ET.ParseError as e:
                messages.error(request, f'Ошибка в XML файле: {str(e)}')
                return redirect('upload_xml')
            
            # Проверяем базовую структуру XML
            routes = tree.findall('route')
            if not routes:
                # Пробуем альтернативные теги
                routes = tree.findall('.//route') or tree.findall('tourist_route') or tree.findall('.//tourist_route')
            
            if not routes:
                messages.error(request, 
                    'В XML файле не найдены маршруты. Ожидаются теги: <route> или <tourist_route>'
                )
                return redirect('upload_xml')
            
            # Строгая проверка первого маршрута на наличие ВСЕХ обязательных полей
            model_fields = get_model_fields()
            required_fields = [field['name'] for field in model_fields if field['required']]
            
            first_route = routes[0]
            missing_fields = []
            
            for field_name in required_fields:
                elem = first_route.find(field_name)
                if elem is None or not elem.text or not elem.text.strip():
                    missing_fields.append(field_name)
            
            if missing_fields:
                messages.error(request, 
                    f'В XML файле отсутствуют обязательные поля: {", ".join(missing_fields)}. '
                    f'Загрузка прервана.'
                )
                return redirect('upload_xml')
            
            # Проверяем валидность данных в первом маршруте
            validation_errors = []
            for field_name in required_fields:
                elem = first_route.find(field_name)
                value = elem.text.strip()
                field_config = next((f for f in model_fields if f['name'] == field_name), None)
                
                if field_config:
                    if field_config['type'] in ['DecimalField']:
                        try:
                            float_value = float(value)
                            if float_value <= 0:
                                validation_errors.append(f"{field_name} должно быть положительным числом")
                        except (ValueError, TypeError):
                            validation_errors.append(f"{field_name} должно быть числом")
                    
                    elif field_config['type'] in ['PositiveIntegerField', 'IntegerField']:
                        try:
                            int_value = int(value)
                            if int_value <= 0:
                                validation_errors.append(f"{field_name} должно быть положительным целым числом")
                        except (ValueError, TypeError):
                            validation_errors.append(f"{field_name} должно быть целым числом")
            
            if validation_errors:
                messages.error(request, 
                    f'Обнаружены ошибки в данных: {", ".join(validation_errors)}. '
                    f'Загрузка прервана.'
                )
                return redirect('upload_xml')
            
            # Сохраняем новый файл
            with open(XML_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            # Загружаем данные из XML с строгой проверкой
            try:
                loaded_count = load_routes_from_xml()
                messages.success(request, f'XML файл успешно загружен! Загружено {loaded_count} маршрутов.')
            except ValueError as e:
                # Откатываем изменения - удаляем файл если загрузка не удалась
                if os.path.exists(XML_FILE_PATH):
                    os.remove(XML_FILE_PATH)
                ensure_xml_file_exists()
                messages.error(request, str(e))
                
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

def validate_xml_structure(xml_content):
    """Проверяет структуру XML файла перед загрузкой"""
    try:
        root = ET.fromstring(xml_content)
        
        # Получаем информацию о полях модели
        model_fields = get_model_fields()
        required_fields = [field['name'] for field in model_fields if field['required']]
        
        # Ищем маршруты
        routes = root.findall('route') or root.findall('.//route')
        
        if not routes:
            return False, "В XML не найдены маршруты (тег <route>)"
        
        # Проверяем первый маршрут на наличие обязательных полей
        first_route = routes[0]
        missing_fields = []
        
        for field_name in required_fields:
            if first_route.find(field_name) is None:
                missing_fields.append(field_name)
        
        if missing_fields:
            return False, f"Отсутствуют обязательные поля: {', '.join(missing_fields)}"
        
        return True, "XML структура корректна"
        
    except ET.ParseError as e:
        return False, f"Ошибка парсинга XML: {str(e)}"
    
    
def validate_xml_before_upload(xml_content):
    """Строгая проверка XML файла перед загрузкой"""
    try:
        root = ET.fromstring(xml_content)
        
        # Получаем информацию о полях модели
        model_fields = get_model_fields()
        required_fields = [field['name'] for field in model_fields if field['required']]
        
        # Ищем маршруты
        routes = root.findall('route') or root.findall('.//route')
        
        if not routes:
            return False, "В XML не найдены маршруты (тег <route>)"
        
        errors = []
        
        # Проверяем каждый маршрут
        for i, route in enumerate(routes, 1):
            route_errors = []
            
            # Проверяем обязательные поля
            for field_name in required_fields:
                elem = route.find(field_name)
                if elem is None:
                    route_errors.append(f"отсутствует поле '{field_name}'")
                elif not elem.text or not elem.text.strip():
                    route_errors.append(f"поле '{field_name}' пустое")
                else:
                    # Проверяем валидность данных
                    value = elem.text.strip()
                    field_config = next((f for f in model_fields if f['name'] == field_name), None)
                    
                    if field_config:
                        if field_config['type'] in ['DecimalField']:
                            try:
                                float_value = float(value)
                                if float_value <= 0:
                                    route_errors.append(f"поле '{field_name}' должно быть положительным числом")
                            except (ValueError, TypeError):
                                route_errors.append(f"поле '{field_name}' должно быть числом")
                        
                        elif field_config['type'] in ['PositiveIntegerField', 'IntegerField']:
                            try:
                                int_value = int(value)
                                if int_value <= 0:
                                    route_errors.append(f"поле '{field_name}' должно быть положительным целым числом")
                            except (ValueError, TypeError):
                                route_errors.append(f"поле '{field_name}' должно быть целым числом")
            
            if route_errors:
                errors.append(f"Маршрут #{i}: {', '.join(route_errors)}")
        
        if errors:
            return False, "Обнаружены ошибки:\n" + "\n".join(errors)
        
        return True, f"XML файл корректен. Найдено {len(routes)} маршрутов."
        
    except ET.ParseError as e:
        return False, f"Ошибка парсинга XML: {str(e)}"