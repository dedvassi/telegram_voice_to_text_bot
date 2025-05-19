# Инструкция по установке шрифтов для Windows

Для корректной работы функции генерации PDF-протоколов на Windows необходимо установить шрифты Liberation Sans.

## Автоматическая установка

1. Скачайте архив с шрифтами Liberation Sans:
   - [Скачать Liberation Sans](https://github.com/liberationfonts/liberation-fonts/files/7261482/liberation-fonts-ttf-2.1.5.tar.gz)

2. Распакуйте архив и найдите файлы:
   - `LiberationSans-Regular.ttf`
   - `LiberationSans-Bold.ttf`

3. Скопируйте эти файлы в папку `fonts` в директории проекта:
   ```
   C:\путь\к\проекту\telegram_voice_to_text_bot\fonts\
   ```

4. Если папки `fonts` не существует, создайте её.

## Ручная установка из системных шрифтов

Если у вас уже установлены шрифты Liberation Sans в системе:

1. Создайте папку `fonts` в корне проекта:
   ```
   mkdir fonts
   ```

2. Скопируйте шрифты из системной папки:
   ```
   copy C:\Windows\Fonts\LiberationSans-Regular.ttf fonts\
   copy C:\Windows\Fonts\LiberationSans-Bold.ttf fonts\
   ```

## Альтернативные шрифты

Если у вас нет шрифтов Liberation Sans, вы можете использовать другие шрифты с поддержкой кириллицы:

1. Arial (обычно уже установлен в Windows):
   ```
   copy C:\Windows\Fonts\arial.ttf fonts\LiberationSans-Regular.ttf
   copy C:\Windows\Fonts\arialbd.ttf fonts\LiberationSans-Bold.ttf
   ```

2. DejaVu Sans:
   - [Скачать DejaVu Sans](https://dejavu-fonts.github.io/Files/dejavu-sans-ttf-2.37.zip)

## Проверка установки

После установки шрифтов перезапустите бота и проверьте работу функции генерации протоколов командой `/protocol`.
