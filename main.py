import flet as ft
import sys
import json
import logging
import zipfile
import os
import send2trash


version = 'v1.2'
config_file = {'dir_path': '', 'width': 1280,
               'height': 800, 'top': 0, 'left': 0}
cover_config_file = dict()
dir_photos = ''  # Diretório raiz do arquivo de imagens
people_list = []
image_list = dict()
loading_ok = False
dir_exclude = ['.thumb.stogram', '.thumbs.videos']
scroll_position = 0

config_locate = os.path.join(os.path.expanduser('~'), 'photogram_configs.cfg')

# ----------------------- SISTEMA DE LOG ---------------------------------------------
# Cria um logger
log = logging.getLogger('Log')
log.setLevel(logging.DEBUG)  # Define o nível de log para DEBUG

# Cria um manipulador de arquivos que registra até o nível DEBUG
handler = logging.FileHandler('info.log', encoding='utf-8')
handler.setLevel(logging.DEBUG)

# Cria um manipulador de console que registra até o nível INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Cria um formato de log
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Adiciona os manipuladores ao log
log.addHandler(handler)
log.addHandler(console_handler)

# Mensagens de log
# log.debug('mensagem de debug')
# log.info('mensagem de informação')
# log.warning('mensagem de aviso')
# log.error('mensagem de erro')
# log.critical('mensagem crítica')

# Instalando FFMPEG caso não possua no PC
if not os.path.isfile(os.path.join(os.path.expanduser('~'), ".photogram/ffmpeg.exe")):
    log.warning('FFMPEG não encontrado, instalando...')
    caminho_atual = os.getcwd()
    zipFile = caminho_atual + '\\ffmpeg.zip'
    try:
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extractall(os.path.join(os.path.expanduser('~'), ".photogram"))
        log.info("FFMPEG instalado com sucesso.")

    except Exception as e:
        log.error(f"Erro descompactar ffmpeg. Erro:{str(e)}")
else:
    log.info(f"FFMPEG já instalado.")

# esse os.environ tem q ficar antes do import do VideoFileClip!    
os.environ["IMAGEIO_FFMPEG_EXE"] = os.path.join(os.path.expanduser('~'), ".photogram/ffmpeg") 
from moviepy.editor import VideoFileClip

def save_config():
    global config_file
    global dir_photos

    try:
        with open(config_locate, 'w') as file:
            json.dump(config_file, file)
            dir_photos = config_file['dir_path']
    except Exception as e:
        log.error(f'Não foi possível salvar as configs gerais. Erro: {str(e)}')

    log.info('Configs gerais salvas')


def save_thumb_config():
    global cover_config_file

    dir_main = os.path.join(config_file['dir_path'], 'thumbs_config.cfg')
    try:
        with open(dir_main, 'w') as file:
            json.dump(cover_config_file, file)
    except Exception as e:
        log.error(
            f'Não foi possível salvar as configs de thumbs. Erro: {str(e)}')

    log.info('Thumbs configs salvas')


def read_thumbs_config():
    global cover_config_file

    dir_thumbs_config = os.path.join(
        config_file['dir_path'], 'thumbs_config.cfg')
    if not os.path.exists(dir_thumbs_config):
        save_thumb_config()
    try:
        with open(dir_thumbs_config, 'r') as file:
            cover_config_file = json.load(file)
        log.info('Configuração de capas carregada com sucesso.')
    except Exception as e:
        log.error(f'Configuração de capas NÃO carregada. Erro: {str(e)}')
        return False
    return True


def read_config():
    global config_file

    if not os.path.exists(config_locate):
        save_config()
    else:
        try:
            with open(config_locate, 'r') as file:
                config_file = json.load(file)
            log.info('Configuração inicial carregada com sucesso.')
        except Exception as e:
            log.error(f'Configuração inicial NÃO carregada. Erro: {str(e)}')

        if config_file['dir_path'] == '':
            log.warning(
                'Configuração default inexistente. Não carregar programa')
            return False

        return read_thumbs_config()
    return False


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def criar_thumbnail(caminho_video, tempo, caminho_thumbnail):
    try:
        clip = VideoFileClip(caminho_video)
    except Exception as e:
        log.error(f'Erro ao criar objeto VideoFileClip de {str(caminho_video)}. Erro: {str(e)}')

    try:
        # Salva o frame como uma imagem
        clip.save_frame(caminho_thumbnail, tempo)
    except Exception as e:
        log.error(f'Erro ao salvar a miniatura do video {str(caminho_thumbnail)}. Erro: {str(e)}')

    clip.close()


def is_video(path):
    if path[-4:] == '.mp4':
        return True
    if path[-4:] == '.mpeg':
        return True
    return False


def thumb_path(people, path):
    people_position = path.find(people)
    file_name = path.rfind('\\')
    path_new = path[:people_position] + people + \
        '\\.thumbs.videos' + path[file_name:] + '.video.jpg'
    return path_new


def start(percent, page):
    global dir_photos
    global loading_ok
    dir_photos = config_file['dir_path']

    # Colocando as pastas da raíz na lista people_list e como chave do dicionário de capas
    for folder in os.listdir(dir_photos):
        if os.path.isdir(dir_photos + '\\' + folder):
            people_list.append(folder)
            if folder not in cover_config_file:
                cover_config_file[folder] = ''

    for folder in people_list:
        img_list = []
        dir_folder = dir_photos + '\\' + folder
        dir_thumbs = dir_folder + '\\.thumbs.videos'

        if not os.path.exists(dir_thumbs):
            os.makedirs(dir_thumbs)

        if os.path.isdir(dir_folder):
            for directory_path, directory_names, file_names in os.walk(dir_folder):
                directory_names[:] = [
                    d for d in directory_names if d not in dir_exclude]

                position_control = list()
                for file_name in file_names:
                    dir_file = os.path.join(directory_path, file_name)

                    if dir_file[-4:] == '.mp4' or dir_file[-4:] == 'mpeg':
                        video_input_path = dir_file
                        img_output_path = dir_thumbs + '\\' + file_name + '.video.jpg'

                        try:
                            if not os.path.isfile(img_output_path):
                                criar_thumbnail(video_input_path, "00:00:0.10", img_output_path)
                        except Exception as e:
                            log.error(
                                f'Erro ao criar miniatrura. Erro: {str(e)}')
                        else:
                            if len(position_control) == 0:
                                    position_control.append(file_name)
                            else:
                                for i in range (len(position_control)):
                                    if file_name > position_control[i]:        
                                        position_control.insert(i, file_name)
                                        img_list.insert(i, dir_file)
                                        break

                    else:
                        if len(position_control) == 0:
                                position_control.append(file_name)
                        else:
                            for i in range (len(position_control)):
                                if file_name > position_control[i]:        
                                    position_control.insert(i, file_name)
                                    img_list.insert(i, dir_file)
                                    break
                    percent.value = dir_file
                    page.update()

        image_list[folder] = img_list
        if cover_config_file[folder] == '':
            for i in img_list:
                if i[-4:] == '.jpg':
                    cover_config_file[folder] = i
                    break

    loading_ok = True

# ----------------------------------------------------------------------------------------------------------------------------- CONFIG SCREEN -------------


def config_screen(page: ft.page):
    page.title = 'Photogram ' + version

    def get_directory_result(e: ft.FilePickerResultEvent):
        config_file['dir_path'] = e.path if e.path else "Você tem que selecionar uma pasta!"
        directory_path.value = config_file['dir_path']
        directory_path.color = ft.colors.GREEN
        directory_path.update()

    def confirming_directory(e):
        global loading_ok

        save_config()
        loading_ok = True
        page.window_destroy()
        restart_program()

    get_directory_dialog = ft.FilePicker(on_result=get_directory_result)
    page.overlay.extend([get_directory_dialog])

    layout = ft.Container(
        ft.Column(
            controls=[
                ft.Text("Selecionando pasta", size=28),
                ft.Divider(),
                ft.Text('Selecione o local das imagens e videos.', size=20),
                directory_path := ft.Text(config_file['dir_path'], color=ft.colors.YELLOW),
                ft.Divider(),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            "Localizar Pasta...", on_click=lambda _: get_directory_dialog.get_directory_path()),
                        ft.OutlinedButton(
                            "Salvar e Fechar", on_click=confirming_directory, disabled=False),
                    ],
                    alignment=ft.MainAxisAlignment.END)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(220, 220, 220, 20),
    )
    page.add(layout)
    page.update()

# ----------------------------------------------------------------------------------------------------------------------------- MAIN SCREEN -------------


def main(page: ft.Page):
    page.title = 'Photogram ' + version
    page.window_width = config_file['width']
    page.window_height = config_file['height']
    page.window_left = config_file['left']
    page.window_top = config_file['top']
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_title_bar_hidden = True

    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(
            track_color={
                ft.MaterialState.HOVERED: '#33000000',
                ft.MaterialState.DEFAULT: ft.colors.TRANSPARENT,
            },
            track_visibility=True,
            track_border_color=ft.colors.TRANSPARENT,
            thumb_visibility=True,
            thumb_color={
                ft.MaterialState.HOVERED: '#FFFFFFFF',
                ft.MaterialState.DEFAULT: '#44FFFFFF',
            },
            thickness=10,
            radius=100,
            main_axis_margin=0,
            cross_axis_margin=0,
        )
    )

    progress = ft.ProgressBar(width=page.window_width, color=ft.colors.GREEN)
    texto = ft.Text("Carregando Miniaturas ...")
    percent = ft.Text("")

    def on_column_scroll(e: ft.OnScrollEvent):
        global scroll_position
        scroll_position = e.pixels

    def close_app(e):
        ''' Fecha o Aplicativo '''
        global config_file
        config_file['width'] = page.window_width
        config_file['height'] = page.window_height
        config_file['left'] = page.window_left
        config_file['top'] = page.window_top
        save_config()
        save_thumb_config()
        page.views.clear()
        page.window_destroy()
        sys.exit()

    def minimize_app(e):
        ''' Minimiza o Aplicativo '''
        page.window_minimized = True
        page.update()

    def maximize_app(e):
        ''' Maximiza o Aplicativo '''
        page.window_maximized = not page.window_maximized
        page.update()

    appbar_default = ft.AppBar(
        toolbar_height=40,
        title=ft.WindowDragArea(
            ft.Container(
                content=ft.Text('Photogram', size=18,
                                color=ft.colors.WHITE),
                alignment=ft.alignment.center_left,
                height=30,
            ),
            maximizable=True,
            expand=True,
        ),
        bgcolor=ft.colors.SHADOW,
        actions=[
            ft.Container(
                content=ft.IconButton(
                    icon=ft.icons.MINIMIZE, tooltip="Minimizar", on_click=minimize_app, icon_size=18, icon_color=ft.colors.WHITE, style=ft.ButtonStyle(bgcolor={ft.MaterialState.HOVERED: ft.colors.WHITE12}, shape={ft.MaterialState.HOVERED: ft.RoundedRectangleBorder(radius=0)})),
                alignment=ft.alignment.center_right,
            ),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.icons.CROP_SQUARE_ROUNDED, tooltip="Maximizar", on_click=maximize_app, icon_size=18, icon_color=ft.colors.WHITE, style=ft.ButtonStyle(bgcolor={ft.MaterialState.HOVERED: ft.colors.WHITE12}, shape={ft.MaterialState.HOVERED: ft.RoundedRectangleBorder(radius=0)})),
                alignment=ft.alignment.center_right,
            ),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.icons.CLOSE, tooltip="Fechar APP", on_click=close_app, icon_size=18, icon_color=ft.colors.WHITE, style=ft.ButtonStyle(bgcolor={ft.MaterialState.HOVERED: ft.colors.RED}, shape={ft.MaterialState.HOVERED: ft.RoundedRectangleBorder(radius=0)})),
                alignment=ft.alignment.center_right,
            )
        ],
    )

    page.add(texto, progress, percent)
    page.update()
    start(percent, page)
    progress.visible = False
    page.update()

    grid = ft.GridView(
        expand=1,
        runs_count=5,
        max_extent=220,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
        padding=ft.Padding(0,0,20,0),
    )
    

    page.add(grid)

    def open_imagem(e):
        img = e.control.data['img_dir']
        log.info(f'abrindo {img}')
        os.startfile(img)
        page.update()

    def route_page(e):
        page.go(e.control.key)

    page.snack_bar = ft.SnackBar(
        content=ft.Text(""),
        # action="Alright!",
    )

    def snack_bar_click(text, e):
        page.snack_bar = ft.SnackBar(ft.Text(text))
        page.snack_bar.open = True
        page.update()

    def change_cover_image(e):
        global cover_config_file

        people = e.control.data['people']
        img = e.control.data['img_dir']

        if img[-4:] != '.jpg':
            cover_config_file[people] = thumb_path(people, img)

        else:
            cover_config_file[people] = img

        snack_bar_click('Capa modificada!', e)

        for i in page.views[0].controls[0].controls:
            if i.key == people:
                i.content.controls[0].src = cover_config_file[people]
        page.update()

    for people in image_list:
        images_count = len(image_list[people])

        grid.controls.append(
            ft.Container(
                content=ft.Stack(
                    [
                        ft.Image(
                            src=cover_config_file[people],
                            fit=ft.ImageFit.COVER,
                            repeat=ft.ImageRepeat.NO_REPEAT,
                            border_radius=ft.border_radius.all(10),
                            width=220,
                            height=220,
                        ),
                        ft.Column(
                            [
                                ft.Stack(
                                    [
                                        ft.Text(
                                            spans=[
                                                ft.TextSpan(
                                                    people,
                                                    ft.TextStyle(
                                                        color=ft.colors.WHITE,
                                                        size=16,
                                                        weight="bold",
                                                        foreground=ft.Paint(
                                                            color=ft.colors.BLACK,
                                                            stroke_width=3,
                                                            stroke_join=ft.StrokeJoin.ROUND,
                                                            style=ft.PaintingStyle.STROKE,
                                                        ),
                                                    ),
                                                ),
                                            ],
                                        ),
                                        ft.Text(
                                            spans=[
                                                ft.TextSpan(
                                                    people,
                                                    ft.TextStyle(
                                                        color=ft.colors.WHITE,
                                                        size=16,
                                                        weight="bold",
                                                    ),
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            width=220,
                            height=180,
                        ),
                        ft.Container(
                            content=ft.Text(
                                images_count,
                                weight=ft.FontWeight.W_600
                            ),
                            top=5,
                            right=5,
                            visible=True,
                            bgcolor=ft.colors.RED,
                            alignment=ft.alignment.center,
                            border_radius=ft.border_radius.all(15),
                            padding=ft.Padding(5, 0, 5, 2)
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.icons.OPEN_IN_FULL,
                                on_click=route_page,
                                key=people,
                                width=40,
                                style=ft.ButtonStyle(
                                    color=ft.colors.TRANSPARENT,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=10),
                                ),
                            ),
                            width=220,
                            height=220,
                        ),
                    ],
                ),
                key=people, # Chave para poder decrementar o badge de qtd
            )
        )

        
    def del_imagem(e):
        global grid_images
        people = e.control.data[0]
        img = e.control.data[1]

        if is_video(img):
            if cover_config_file[people] == thumb_path(people, img):
                snack_bar_click(
                    'Imagem da Capa, selecione outra antes de apagar!', e)
                return False

        if cover_config_file[people] == img:
            snack_bar_click(
                'Imagem da Capa, selecione outra antes de apagar!', e)
            return False

        if os.path.isfile(img):
            try:
                send2trash.send2trash(img)
            except Exception as e:
                log.error(f'Erro ao remover imagem {img}. Erro: {str(e)}')
            else:
                log.info(f'removendo arquivo {img}')

            if is_video(img):
                isVideo = thumb_path(people, img)
                if os.path.isfile(isVideo):
                    try:
                        send2trash.send2trash(isVideo)
                    except Exception as e:
                        log.error(f'Erro ao remover video {isVideo}. Erro: {str(e)}')
                    else:
                        log.info(f'removendo thumb {isVideo}')

            image_list[people].remove(img)

            for i in page.views[1].controls[0].controls:
                if i.key == img:
                    page.views[1].controls[0].controls.remove(i)

            for i in page.views[0].controls[0].controls:
                if i.key == people:
                    i.content.controls[2].content.value = len(
                        image_list[people])

            # grid.scroll_to(offset=scroll_position)
            page.update()
        else:
            log.info(f"Arquivo inexistente {img}")
        return True

    def image_container(dir_thumb, dir_photo, radius, people):
        return ft.Container(
                    content=ft.Stack(
                        [
                            ft.Image(
                                src=dir_thumb,
                                fit=ft.ImageFit.COVER,
                                repeat=ft.ImageRepeat.NO_REPEAT,
                                border_radius=ft.border_radius.all(radius),
                                width=220,
                                height=220,
                            ),
                            ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.OPEN_IN_FULL,
                                    data={'img_dir': dir_photo,
                                        'people': people},
                                    on_click=open_imagem,
                                    width=40,
                                    style=ft.ButtonStyle(
                                        color=ft.colors.TRANSPARENT,
                                        shape=ft.RoundedRectangleBorder(
                                            radius=10),
                                    ),
                                ),
                                width=220,
                                height=220,
                                data={'img_dir': dir_photo, 'people': people},
                                on_long_press=change_cover_image
                            ),
                            ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.DELETE_FOREVER_SHARP,
                                    on_click=del_imagem,
                                    data=[people, dir_photo],
                                    width=40,
                                    style=ft.ButtonStyle(
                                        color={
                                            ft.MaterialState.DEFAULT: ft.colors.WHITE,
                                            ft.MaterialState.HOVERED: ft.colors.RED,
                                        },
                                        bgcolor={
                                            ft.MaterialState.HOVERED: ft.colors.WHITE},
                                        shape=ft.RoundedRectangleBorder(
                                            radius=100),
                                    ),
                                ),
                                bottom=5,
                                right=5,
                                width=40,
                                height=40,
                                visible=True,
                            ),
                        ],
                    ),
                    key=dir_photo,
                ),

    def people_images(people):
        '''
        Cria um grid com todas as imagens de acordo com a pessoa passada como parâmetro

        '''
        progress.width = page.window_width
        progress.visible = True
        page.update()

        grid = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=220,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            on_scroll=on_column_scroll,
            padding=ft.Padding(0,0,20,0),
        )

        for dir_photo in image_list[people]:
            dir_thumb = dir_photo

            radius = 10
            if is_video(dir_photo):
                radius = 100
                dir_thumb = thumb_path(people, dir_photo)

            # grid.controls.append(image_container(dir_thumb, dir_photo, radius, people))

            grid.controls.append( 
                ft.Container(
                    content=ft.Stack(
                        [
                            ft.Image(
                                src=dir_thumb,
                                fit=ft.ImageFit.COVER,
                                repeat=ft.ImageRepeat.NO_REPEAT,
                                border_radius=ft.border_radius.all(radius),
                                width=220,
                                height=220,
                            ),
                            ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.OPEN_IN_FULL,
                                    data={'img_dir': dir_photo,
                                          'people': people},
                                    on_click=open_imagem,
                                    width=40,
                                    style=ft.ButtonStyle(
                                        color=ft.colors.TRANSPARENT,
                                        shape=ft.RoundedRectangleBorder(
                                            radius=10),
                                    ),
                                ),
                                width=220,
                                height=220,
                                data={'img_dir': dir_photo, 'people': people},
                                on_long_press=change_cover_image
                            ),
                            ft.Container(
                                content=ft.IconButton(
                                    icon=ft.icons.DELETE_FOREVER_SHARP,
                                    on_click=del_imagem,
                                    data=[people, dir_photo],
                                    width=40,
                                    style=ft.ButtonStyle(
                                        color={
                                            ft.MaterialState.DEFAULT: ft.colors.WHITE,
                                            ft.MaterialState.HOVERED: ft.colors.RED,
                                        },
                                        bgcolor={
                                            ft.MaterialState.HOVERED: ft.colors.WHITE},
                                        shape=ft.RoundedRectangleBorder(
                                            radius=100),
                                    ),
                                ),
                                bottom=5,
                                right=5,
                                width=40,
                                height=40,
                                visible=True,
                            ),
                        ],
                    ),
                    key=dir_photo,
                ),
            )

        return grid

# ----------------------------------------------------------------------------------------------------------------------------- ALTERANDO PASTA -------------
    def get_directory_result(e: ft.FilePickerResultEvent):
        config_file['dir_path'] = e.path if e.path else "Você tem que selecionar uma pasta!"
        directory_path.value = config_file['dir_path']
        directory_path.color = ft.colors.GREEN
        directory_path.update()

    def confirming_directory(e):

        save_config()

        page.window_destroy()
        restart_program()

    get_directory_dialog = ft.FilePicker(on_result=get_directory_result)
    page.overlay.extend([get_directory_dialog])

    def close_loading_folder_modal(e):
        config_folder_modal.open = False
        page.update()

    config_folder_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("Selecionando pasta"),
        content=ft.Text("Selecione o local das imagens e videos."),
        actions=[
            ft.Column(
                [
                    directory_path := ft.Text(config_file['dir_path'], color=ft.colors.LIGHT_GREEN),
                    ft.Divider(),
                    ft.Row(
                        [
                            ft.OutlinedButton(
                                "Localizar Pasta...", on_click=lambda _: get_directory_dialog.get_directory_path()),
                            ft.OutlinedButton(
                                "Salvar e Fechar", on_click=confirming_directory,),
                            ft.OutlinedButton(
                                "Cancelar", on_click=close_loading_folder_modal,),
                        ]
                    )
                ]
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def loading_folder(e):
        page.dialog = config_folder_modal
        config_folder_modal.open = True
        save_thumb_config()
        page.update()

    floatingButton = ft.FloatingActionButton(
        icon=ft.icons.FOLDER_OPEN_SHARP, on_click=loading_folder, bgcolor=ft.colors.BLACK
    )
# ----------------------------------------------------------------------------------------------------------------------------- ALTERANDO PASTA FIM -------------

    def layout(e):
        page.views.clear()
        appbar_default.title.content.content.value = 'Photogram ' + version
        page.views.append(
            ft.View(
                '/',
                [
                    grid,
                    progress,
                ],
                floating_action_button=floatingButton,
                appbar=appbar_default
            )
        )

        progress.visible = False
        page.update()

        if page.route in people_list:

            appbar_default.title.content.content.value += ' | ' + page.route
            grid_images = people_images(page.route)

            page.views.append(
                ft.View(
                    page.route,
                    [
                        grid_images
                    ],
                    appbar=appbar_default,
                )
            )

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = layout
    page.on_view_pop = view_pop
    page.go(page.route)


if not read_config() and not loading_ok:
    ft.app(target=config_screen)
else:
    ft.app(target=main)
