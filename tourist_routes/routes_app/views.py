import os
import xml.etree.ElementTree as ET
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db import models, IntegrityError
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .models import TouristRoute

XML_FILE_PATH = os.path.join(settings.BASE_DIR, 'media', 'tourist_routes.xml')

def ensure_xml_file_exists():
    """Создает XML файл если его нет"""
    os.makedirs(os.path.dirname(XML_FILE_PATH), exist_ok=True)
    if not os.path.exists(XML_FILE_PATH):
        root = ET.Element('tourist_routes')
        root.set('version', '1.0')
        root.set('created', datetime.now().isoformat())
        tree = ET.ElementTree(root)
        tree.write(XML_FILE_PATH, encoding='utf-8', xml_declaration=True)

def save_route_to_xml(route_data):
    """Сохраняет маршрут в XML файл"""
    ensure_xml_file_exists()
    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        
        # Проверка дубликатов в XML
        for existing_route in root.findall('route'):
            existing_name = existing_route.find('name')
            existing_region = existing_route.find('region')
            if (existing_name is not None and existing_name.text == route_data['name'] and 
                existing_region is not None and existing_region.text == route_data['region']):
                return False
        
        # Добавляем новый маршрут
        route_elem = ET.SubElement(root, 'route')
        
        # Сохраняем все поля
        ET.SubElement(route_elem, 'name').text = route_data['name']
        ET.SubElement(route_elem, 'description').text = route_data['description']
        ET.SubElement(route_elem, 'length_km').text = str(route_data['length_km'])
        ET.SubElement(route_elem, 'duration_days').text = str(route_data['duration_days'])
        ET.SubElement(route_elem, 'difficulty').text = route_data['difficulty']
        ET.SubElement(route_elem, 'region').text = route_data['region']
        ET.SubElement(route_elem, 'best_season').text = route_data['best_season']
        ET.SubElement(route_elem, 'kolvo_chel').text = str(route_data['kolvo_chel'])
        ET.SubElement(route_elem, 'created_at').text = datetime.now().isoformat()
        
        root.set('last_updated', datetime.now().isoformat())
        tree.write(XML_FILE_PATH, encoding='utf-8', xml_declaration=True)
        return True
        
    except ET.ParseError:
        ensure_xml_file_exists()
        return save_route_to_xml(route_data)

def get_routes_from_xml():
    """Получает маршруты напрямую из XML файла"""
    ensure_xml_file_exists()
    try:
        tree = ET.parse(XML_FILE_PATH)
        root = tree.getroot()
        
        routes = []
        for route_elem in root.findall('route'):
            try:
                route_data = {}
                
                # Извлекаем данные из XML
                fields = ['name', 'description', 'length_km', 'duration_days', 
                         'difficulty', 'region', 'best_season', 'kolvo_chel', 'created_at']
                
                for field in fields:
                    elem = route_elem.find(field)
                    if elem is not None and elem.text:
                        route_data[field] = elem.text
                    else:
                        route_data[field] = ''
                
                # Проверяем что есть обязательные поля
                if (route_data['name'] and route_data['description'] and 
                    route_data['length_km'] and route_data['duration_days'] and
                    route_data['difficulty'] and route_data['region']):
                    routes.append(route_data)
                    
            except Exception as e:
                continue
                
        return routes
                    
    except ET.ParseError:
        ensure_xml_file_exists()
        return []

def validate_route_data(data):
    """Валидация данных маршрута"""
    errors = []
    
    if not data.get('name') or not data['name'].strip():
        errors.append("Название маршрута обязательно")
    
    if not data.get('description') or not data['description'].strip():
        errors.append("Описание маршрута обязательно")
    
    try:
        length = float(data.get('length_km', 0))
        if length <= 0:
            errors.append("Протяженность должна быть положительным числом")
    except (ValueError, TypeError):
        errors.append("Протяженность должна быть числом")
    
    try:
        duration = int(data.get('duration_days', 0))
        if duration <= 0:
            errors.append("Продолжительность должна быть положительным числом")
    except (ValueError, TypeError):
        errors.append("Продолжительность должна быть целым числом")
    
    if not data.get('difficulty') or data['difficulty'] not in ['легкий', 'средний', 'сложный']:
        errors.append("Укажите корректную сложность маршрута")
    
    if not data.get('region') or not data['region'].strip():
        errors.append("Регион обязателен")
    
    return errors

def index(request):
    return render(request, 'routes_app/index.html')

def add_route(request):
    if request.method == 'POST':
        # Собираем данные из формы
        route_data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'length_km': request.POST.get('length_km', '0'),
            'duration_days': request.POST.get('duration_days', '0'),
            'difficulty': request.POST.get('difficulty', ''),
            'region': request.POST.get('region', '').strip(),
            'best_season': request.POST.get('best_season', '').strip(),
            'kolvo_chel': request.POST.get('kolvo_chel', '0'),
        }
        
        # Валидация
        errors = validate_route_data(route_data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'routes_app/add_route.html', {
                'form_data': route_data,
                'difficulty_choices': TouristRoute.DIFFICULTY_CHOICES
            })
        
        try:
            # Выбираем куда сохранять
            save_to = request.POST.get('save_to', 'db')
            
            if save_to == 'db':
                # Сохраняем в БД
                route = TouristRoute(
                    name=route_data['name'],
                    description=route_data['description'],
                    length_km=float(route_data['length_km']),
                    duration_days=int(route_data['duration_days']),
                    difficulty=route_data['difficulty'],
                    region=route_data['region'],
                    best_season=route_data['best_season'],
                    kolvo_chel=float(route_data['kolvo_chel']),
                    source='db'
                )
                try:
                    route.save()
                    messages.success(request, f'Маршрут "{route.name}" сохранен в базу данных!')
                except IntegrityError:
                    messages.warning(request, f'Маршрут "{route.name}" уже существует в базе данных!')
                    
            elif save_to == 'xml':
                # Сохраняем в XML
                route_data_for_xml = {
                    'name': route_data['name'],
                    'description': route_data['description'],
                    'length_km': float(route_data['length_km']),
                    'duration_days': int(route_data['duration_days']),
                    'difficulty': route_data['difficulty'],
                    'region': route_data['region'],
                    'best_season': route_data['best_season'],
                    'kolvo_chel': float(route_data['kolvo_chel']),
                }
                
                if save_route_to_xml(route_data_for_xml):
                    messages.success(request, f'Маршрут "{route_data["name"]}" сохранен в XML файл!')
                else:
                    messages.warning(request, f'Маршрут "{route_data["name"]}" уже существует в XML файле!')
            
            return redirect('routes_list')
            
        except Exception as e:
            messages.error(request, f'Ошибка при сохранении: {str(e)}')
            return render(request, 'routes_app/add_route.html', {
                'form_data': route_data,
                'difficulty_choices': TouristRoute.DIFFICULTY_CHOICES
            })
    
    return render(request, 'routes_app/add_route.html', {
        'difficulty_choices': TouristRoute.DIFFICULTY_CHOICES
    })

def routes_list(request):
    source = request.GET.get('source', 'db')
    search_query = request.GET.get('search', '')
    
    if source == 'xml':
        # Получаем маршруты напрямую из XML файла
        xml_routes = get_routes_from_xml()
        
        # Применяем поиск если нужно
        if search_query:
            xml_routes = [
                route for route in xml_routes 
                if (search_query.lower() in route['name'].lower() or 
                    search_query.lower() in route['description'].lower() or
                    search_query.lower() in route['region'].lower() or
                    search_query.lower() in route['best_season'].lower())
            ]
        
        context = {
            'xml_routes': xml_routes,
            'source': source,
            'search_query': search_query,
        }
        
    else:
        # Данные из БД
        routes = TouristRoute.objects.filter(source='db')
        
        # Поиск для БД
        if search_query:
            routes = routes.filter(
                models.Q(name__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(region__icontains=search_query) |
                models.Q(best_season__icontains=search_query)
            )
        
        routes = routes.order_by('-created_at')
        
        context = {
            'routes': routes,
            'source': source,
            'search_query': search_query,
        }
    
    return render(request, 'routes_app/routes_list.html', context)

@csrf_exempt
def ajax_search(request):
    """AJAX поиск по маршрутам из БД"""
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'results': [], 'message': 'Введите минимум 2 символа'})
        
        try:
            # Ищем по текстовым полям в БД
            routes = TouristRoute.objects.filter(source='db').filter(
                models.Q(name__icontains=query) |
                models.Q(description__icontains=query) |
                models.Q(region__icontains=query) |
                models.Q(best_season__icontains=query) |
                models.Q(difficulty__icontains=query)
            )[:15]  # Ограничиваем количество результатов
            
            results = []
            for route in routes:
                results.append({
                    'id': route.id,
                    'name': route.name,
                    'description': route.description[:100] + '...' if len(route.description) > 100 else route.description,
                    'region': route.region,
                    'length_km': str(route.length_km),
                    'duration_days': route.duration_days,
                    'difficulty': route.get_difficulty_display(),
                    'best_season': route.best_season,
                    'kolvo_chel': str(route.kolvo_chel),
                })
            
            return JsonResponse({
                'results': results,
                'count': len(results),
                'query': query
            })
            
        except Exception as e:
            return JsonResponse({'results': [], 'error': str(e)})
    
    return JsonResponse({'results': [], 'error': 'Invalid request'})

def edit_route(request, route_id):
    """Редактирование маршрута из БД"""
    route = get_object_or_404(TouristRoute, id=route_id, source='db')
    
    if request.method == 'POST':
        route_data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'length_km': request.POST.get('length_km', '0'),
            'duration_days': request.POST.get('duration_days', '0'),
            'difficulty': request.POST.get('difficulty', ''),
            'region': request.POST.get('region', '').strip(),
            'best_season': request.POST.get('best_season', '').strip(),
            'kolvo_chel': request.POST.get('kolvo_chel', '0'),
        }
        
        errors = validate_route_data(route_data)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'routes_app/edit_route.html', {
                'route': route,
                'form_data': route_data,
                'difficulty_choices': TouristRoute.DIFFICULTY_CHOICES
            })
        
        try:
            # Обновляем маршрут
            route.name = route_data['name']
            route.description = route_data['description']
            route.length_km = float(route_data['length_km'])
            route.duration_days = int(route_data['duration_days'])
            route.difficulty = route_data['difficulty']
            route.region = route_data['region']
            route.best_season = route_data['best_season']
            route.kolvo_chel = float(route_data['kolvo_chel'])
            
            route.save()
            messages.success(request, f'Маршрут "{route.name}" успешно обновлен!')
            return redirect('routes_list')
            
        except IntegrityError:
            messages.error(request, 'Маршрут с такими данными уже существует!')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении: {str(e)}')
    
    # GET запрос
    form_data = {
        'name': route.name,
        'description': route.description,
        'length_km': route.length_km,
        'duration_days': route.duration_days,
        'difficulty': route.difficulty,
        'region': route.region,
        'best_season': route.best_season,
        'kolvo_chel': route.kolvo_chel,
    }
    
    return render(request, 'routes_app/edit_route.html', {
        'route': route,
        'form_data': form_data,
        'difficulty_choices': TouristRoute.DIFFICULTY_CHOICES
    })

def delete_route(request, route_id):
    """Удаление маршрута"""
    route = get_object_or_404(TouristRoute, id=route_id)
    
    if request.method == 'POST':
        route_name = route.name
        route.delete()
        messages.success(request, f'Маршрут "{route_name}" удален!')
        return redirect('routes_list')
    
    return render(request, 'routes_app/confirm_delete.html', {'route': route})

def upload_xml(request):
    """Загрузка XML файла"""
    if request.method == 'POST' and request.FILES.get('xml_file'):
        uploaded_file = request.FILES['xml_file']
        
        if not uploaded_file.name.endswith('.xml'):
            messages.error(request, "Поддерживаются только XML файлы")
            return redirect('upload_xml')
        
        try:
            file_content = uploaded_file.read().decode('utf-8')
            ET.fromstring(file_content)  # Проверяем валидность
            
            with open(XML_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            messages.success(request, 'XML файл успешно загружен!')
            return redirect('routes_list')
                
        except ET.ParseError as e:
            messages.error(request, f'Ошибка в XML файле: {str(e)}')
        except Exception as e:
            messages.error(request, f'Ошибка загрузки: {str(e)}')
    
    return render(request, 'routes_app/upload_xml.html')

def download_xml(request):
    """Скачивание XML файла"""
    if not os.path.exists(XML_FILE_PATH):
        messages.error(request, 'XML файл не существует')
        return redirect('routes_list')
    
    from django.http import FileResponse
    response = FileResponse(open(XML_FILE_PATH, 'rb'))
    response['Content-Type'] = 'application/xml'
    response['Content-Disposition'] = f'attachment; filename="tourist_routes_{datetime.now().strftime("%Y%m%d")}.xml"'
    return response