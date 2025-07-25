#!/usr/bin/env python
"""
Script para adicionar valores default corretos em todos os modelos
"""

import os
import re

def fix_datetime_fields():
    """Corrige campos DateTime sem default apropriado"""
    
    # Diretórios dos modelos
    model_files = [
        'soldagem/models.py',
        'qualidade/models.py',
        'core/models.py',
    ]
    
    for file_path in model_files:
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Adicionar import do timezone se não existir
        if 'from django.utils import timezone' not in content:
            content = 'from django.utils import timezone\n' + content
        
        # Corrigir DateTimeField sem default apropriado
        content = re.sub(
            r'DateTimeField\(\)',
            'DateTimeField(auto_now_add=True)',
            content
        )
        
        # Corrigir campos com default vazio
        content = re.sub(
            r"DateTimeField\(default=''\)",
            'DateTimeField(null=True, blank=True)',
            content
        )
        
        # Salvar arquivo corrigido
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Corrigido: {file_path}")

if __name__ == '__main__':
    fix_datetime_fields()
    print("\n✅ Correções aplicadas! Agora execute:")
    print("1. rm -rf */migrations/00*.py (exceto __init__.py)")
    print("2. python manage.py makemigrations")
    print("3. python manage.py migrate")