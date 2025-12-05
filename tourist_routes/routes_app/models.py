from django.db import models

class TouristRoute(models.Model):
    DIFFICULTY_CHOICES = [
        ('легкий', 'Легкий'),
        ('средний', 'Средний'),
        ('сложный', 'Сложный'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Название маршрута")
    description = models.TextField(verbose_name="Описание")
    length_km = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Протяженность (км)")
    duration_days = models.PositiveIntegerField(verbose_name="Продолжительность (дней)")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, verbose_name="Сложность")
    region = models.CharField(max_length=100, verbose_name="Регион")
    best_season = models.CharField(max_length=100, verbose_name="Лучшее время для похода", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    kolvo_chel = models.DecimalField(max_digits=6, decimal_places=2,verbose_name="Количество человек", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=10, choices=[('db', 'База данных'), ('xml', 'XML файл')], default='db', verbose_name="Источник данных")
    
    class Meta:
        unique_together = ['name', 'region', 'length_km']

    def __str__(self):
        return self.name