#!/usr/bin/env python3
"""
Конвертация документации из Wiki.js в формат Diplodoc.

Что делает:
1. Копирует .md файлы из docs_dump в ru/, убирая фронтматтер Wiki.js
2. Конвертирует ссылки из формата Wiki.js в формат Diplodoc
3. Копирует картинки в ru/assets/images/
4. Обновляет ссылки на картинки в markdown файлах
"""

import os
import re
import shutil
from pathlib import Path

# Настройки
SOURCE_DIR = Path("./docs_dump")
TARGET_DIR = Path("./ru")
IMAGES_DIR = TARGET_DIR / "assets" / "images"

# Расширения изображений
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}


def remove_wikijs_frontmatter(content: str) -> str:
    """Удаляет фронтматтер Wiki.js из начала файла."""
    # Убираем блок между --- и ---
    pattern = r'^---\s*\n.*?\n---\s*\n'
    content = re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)
    
    # Убираем атрибуты Wiki.js типа {.is-warning}, {.is-primary}, {.links-list}
    # Сохраняем переносы строк
    content = re.sub(r'\s*\{\.is-\w+\}\s*\n?', '\n', content)
    content = re.sub(r'\s*\{\.links-list\}\s*\n?', '\n', content)
    
    # Убираем множественные пустые строки
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip() + '\n'


def convert_wikijs_links(content: str, file_path: Path, all_files: dict) -> str:
    """
    Конвертирует ссылки из формата Wiki.js в формат Diplodoc.
    
    Wiki.js формат: [/Эксперты/Поиск-эксперта-на-Флатике](текст)
    Diplodoc формат: [текст](Эксперты/Поиск-эксперта-на-Флатике.md)
    """
    def replace_link(match):
        full_match = match.group(0)
        link_text = match.group(1) if match.group(1) else match.group(2)
        wiki_path = match.group(2) if match.group(1) else match.group(3)
        
        # Убираем начальный слэш
        wiki_path = wiki_path.lstrip('/')
        
        # Ищем соответствующий файл
        target_file = find_target_file(wiki_path, all_files)
        if target_file:
            # Относительный путь от текущего файла
            rel_path = get_relative_path(file_path, target_file)
            return f"[{link_text}]({rel_path})"
        else:
            # Если файл не найден, оставляем как есть, но убираем начальный слэш
            return f"[{link_text}]({wiki_path}.md)"
    
    # Паттерн для ссылок Wiki.js: [/path](text) или [text](/path)
    pattern = r'\[([^\]]*)\]\(([^)]+)\)'
    
    def process_link(match):
        link_text = match.group(1)
        link_path = match.group(2)
        
        # Если это ссылка Wiki.js (начинается с /)
        if link_path.startswith('/'):
            wiki_path = link_path.lstrip('/')
            target_file = find_target_file(wiki_path, all_files)
            if target_file:
                rel_path = get_relative_path(file_path, target_file)
                return f"[{link_text}]({rel_path})"
            else:
                # Пробуем найти по имени файла
                return f"[{link_text}]({wiki_path}.md)"
        # Если это уже относительная ссылка или внешняя ссылка
        elif link_path.startswith('http') or link_path.startswith('mailto:'):
            return match.group(0)  # Оставляем как есть
        # Если это ссылка на изображение
        elif any(link_path.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
            # Обновляем путь к изображению
            image_name = os.path.basename(link_path)
            new_path = f"assets/images/{image_name}"
            return f"[{link_text}]({new_path})"
        else:
            return match.group(0)  # Оставляем как есть
    
    content = re.sub(pattern, process_link, content)
    return content


def find_target_file(wiki_path: str, all_files: dict) -> Path:
    """Находит целевой файл по пути Wiki.js."""
    # Пробуем разные варианты
    variants = [
        wiki_path,
        wiki_path.replace('-', ' '),
        wiki_path.replace(' ', '-'),
    ]
    
    for variant in variants:
        # Пробуем найти точное совпадение
        for source_path, target_path in all_files.items():
            source_name = source_path.stem
            if source_name == variant or source_name.replace(' ', '-') == variant:
                return target_path
    
    return None


def get_relative_path(from_file: Path, to_file: Path) -> str:
    """Вычисляет относительный путь от одного файла к другому."""
    from_dir = from_file.parent
    to_file_rel = os.path.relpath(to_file, from_dir)
    # Заменяем обратные слэши на прямые для markdown
    return str(to_file_rel).replace('\\', '/')


def sanitize_filename(name: str) -> str:
    """Очищает имя файла от недопустимых символов."""
    # Заменяем недопустимые символы
    name = name.replace('«', '').replace('»', '')
    # Убираем лишние пробелы
    name = ' '.join(name.split())
    return name


def process_markdown_file(source_path: Path, target_path: Path, all_files: dict):
    """Обрабатывает один markdown файл."""
    print(f"Processing: {source_path} -> {target_path}")
    
    # Читаем исходный файл
    content = source_path.read_text(encoding='utf-8')
    
    # Убираем фронтматтер Wiki.js
    content = remove_wikijs_frontmatter(content)
    
    # Конвертируем ссылки
    content = convert_wikijs_links(content, target_path, all_files)
    
    # Обновляем ссылки на изображения в тексте
    for ext in IMAGE_EXTENSIONS:
        # Паттерн для ссылок на изображения: ![alt](path) или ![](path)
        pattern = rf'!\[([^\]]*)\]\(([^)]+\.{ext[1:]})\)'
        def replace_image(match):
            alt_text = match.group(1)
            image_path = match.group(2)
            image_name = os.path.basename(image_path)
            new_path = f"assets/images/{image_name}"
            return f"![{alt_text}]({new_path})"
        content = re.sub(pattern, replace_image, content, flags=re.IGNORECASE)
    
    # Создаем директорию если нужно
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем файл
    target_path.write_text(content, encoding='utf-8')


def copy_images(source_dir: Path, target_dir: Path):
    """Копирует все изображения из source_dir в target_dir."""
    target_dir.mkdir(parents=True, exist_ok=True)
    
    for ext in IMAGE_EXTENSIONS:
        for image_path in source_dir.rglob(f'*{ext}'):
            if image_path.is_file():
                target_path = target_dir / image_path.name
                print(f"Copying image: {image_path.name}")
                shutil.copy2(image_path, target_path)


def build_file_map(source_dir: Path) -> dict:
    """Строит карту соответствия исходных и целевых файлов."""
    file_map = {}
    
    for md_file in source_dir.rglob('*.md'):
        if md_file.is_file():
            # Вычисляем относительный путь от source_dir
            rel_path = md_file.relative_to(source_dir)
            # Создаем целевой путь
            target_path = TARGET_DIR / rel_path
            file_map[md_file] = target_path
    
    return file_map


def main():
    print("Starting conversion from Wiki.js to Diplodoc...")
    
    if not SOURCE_DIR.exists():
        print(f"Error: Source directory {SOURCE_DIR} does not exist!")
        return
    
    # Строим карту файлов
    print("Building file map...")
    file_map = build_file_map(SOURCE_DIR)
    print(f"Found {len(file_map)} markdown files")
    
    # Копируем изображения
    print("\nCopying images...")
    copy_images(SOURCE_DIR, IMAGES_DIR)
    
    # Обрабатываем markdown файлы
    print("\nProcessing markdown files...")
    for source_path, target_path in file_map.items():
        try:
            process_markdown_file(source_path, target_path, file_map)
        except Exception as e:
            print(f"Error processing {source_path}: {e}")
    
    print("\nConversion complete!")
    print(f"Files copied to: {TARGET_DIR}")
    print(f"Images copied to: {IMAGES_DIR}")


if __name__ == "__main__":
    main()

