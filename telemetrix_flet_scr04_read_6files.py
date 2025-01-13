import time
import csv
from telemetrix import telemetrix
import flet as ft
import asyncio
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart

# Configuração dos pinos do HC-SR04
TRIGGER_PIN = 9
ECHO_PIN = 10

# Variáveis globais
last_distance = None
measurements = []  # Lista para armazenar as últimas medições
error_message = ""

# Callback para capturar a distância medida
def sonar_callback(data):
    global last_distance, error_message
    last_distance = data[2]  # Distância medida em cm
    error_message = ""  # Limpa a mensagem de erro, pois a leitura foi bem-sucedida

# Função para realizar leituras do sensor em tempo real
def perform_readings(board, trigger_pin, echo_pin):
    board.set_pin_mode_sonar(trigger_pin, echo_pin, sonar_callback)


# Função para atualizar o valor da barra gráfica e o texto da distância
def update_distance(page, bar_a5, bar_a5_value, distance_text):
    global last_distance, error_message
    if last_distance is not None:
        distance_text.value = f"Distância: {last_distance:.2f} cm"
        if 0 <= last_distance <= 400:  # Ajuste de gama conforme necessário
            bar_a5.content.controls[1].width = (last_distance / 400) * 280  # Escala baseada em 400 cm
        else:
            bar_a5.content.controls[1].width = 280  # Valor máximo
            distance_text.value += " - Fora da Gama"

        bar_a5_value.value = f"{last_distance:.2f} cm"
        page.update()
    else:
        error_message = "Erro ao obter a distância."



# Função para ler medições de um ficheiro
def read_measurements(file_name, page, table, ax, line_1, line_2):
    try:
        with open(file_name, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Salta a linha de cabeçalho (opcional)
            next(reader)  

            ensaios = []
            horas = []  # Para armazenar os horários das medições
            dist_medidas = []
            dist_reais = []

            for row in reader:
                if len(row) >= 4:
                    ensaios.append(int(row[0]))  # Ensaio Nº
                    horas.append(row[1])        # Hora
                    dist_medidas.append(float(row[2]))  # Distância a Medir
                    dist_reais.append(float(row[3]))    # Distância Real

            # Atualizando a tabela com os dados lidos
            rows = []
            for i in range(len(ensaios)):
                rows.append(ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(value=str(ensaios[i]))),       # Ensaio Nº
                        ft.DataCell(ft.Text(value=str(horas[i]))),        # Hora
                        ft.DataCell(ft.Text(value=str(dist_medidas[i]))), # Distância a Medir
                        ft.DataCell(ft.Text(value=str(dist_reais[i])))    # Distância Real
                    ]
                ))
            table.rows = rows
            page.update()

            # Atualizando o gráfico
            ax.clear()

            ax.plot(ensaios, dist_medidas, color='red', label='Distância a Medir (cm)')
            ax.plot(ensaios, dist_reais, color='blue', label='Distância Real (cm)')

            ax.set_title("Distâncias em função dos Ensaios")
            ax.set_xlabel("Ensaio Nº")
            ax.set_ylabel("Distância (cm)")
            ax.grid(True)
            ax.legend(loc="upper right")

            line_1.set_data(ensaios, dist_medidas)
            line_2.set_data(ensaios, dist_reais)
            
            page.update()

    except Exception as e:
        page.controls.append(
            ft.Text(value=f"Erro ao ler o ficheiro: {str(e)}", size=14, color="red")
        )
        page.update()

# Função principal do Flet
async def main(page: ft.Page):
    global last_distance, measurements

    page.title = "Leitura HC-SR04 com Telemetrix e Flet"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS

    
    distance_text = ft.Text(value="Distância: 0.00 cm", size=16)
    bar_width, bar_height = 280, 50
    bar_a5_value = ft.Text(value="0.00 cm", size=14, color="white")
    bar_a5 = ft.Container(
        content=ft.Stack(
            [
                ft.Container(width=bar_width, height=bar_height, bgcolor="grey"),
                ft.Container(width=0, height=bar_height, bgcolor="red", alignment=ft.alignment.top_left),
                ft.Container(content=bar_a5_value, alignment=ft.alignment.center)
            ]
        ),
        width=bar_width,
        height=bar_height,
    )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Ensaio Nº")),
            ft.DataColumn(ft.Text("Hora")),
            ft.DataColumn(ft.Text("Distância a Medir (cm)")),
            ft.DataColumn(ft.Text("Distância (cm)"))
        ],
        rows=[]  # Inicialmente vazio
    )

    # Container com a tabela
    table_container = ft.Container(
    content=ft.Column(
        controls=[table],
        scroll=ft.ScrollMode.ALWAYS  # Ativando o scroll
    ),
    padding=5,
    border_radius=10,
    border=ft.border.all(2),
    width=600,
    height=600,
    )

    # Criar gráfico de distância
    num_samples = 100
    times = list(range(num_samples))
    graph_distances = [0] * num_samples

    fig, ax = plt.subplots()
    ax.set_xlim(0, 9)  # Limita o eixo X a 9 ensaios
    ax.set_ylim(0, 60)  # Ajusta o limite do eixo Y para a distância

    line_1, = ax.plot([], [], label="Distância a Medir (cm)", color='red')
    line_2, = ax.plot([], [], label="Distância Real (cm)", color='blue')

    ax.grid(True)
    ax.legend(loc="upper right")

    chart = MatplotlibChart(fig, expand=True)

    # Container com o gráfico
    graph_container = ft.Container(
        content=chart,
        padding=5,
        border_radius=10,
        border=ft.border.all(2),
        width=800,
        height=400
    )

    # Botões para leitura de ficheiros
    buttons_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.ElevatedButton(
                        text="Ler Subida 1", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraSubidaSonar1.csv",
                        on_click=lambda e: read_measurements("LeituraSubidaSonar1.csv", page, table, ax, line_1, line_2)
                    ),
                    ft.ElevatedButton(
                        text="Ler Subida 2", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraSubidaSonar2.csv",
                        on_click=lambda e: read_measurements("LeituraSubidaSonar2.csv", page, table, ax, line_1, line_2)
                    ),
                    ft.ElevatedButton(
                        text="Ler Subida 3", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraSubidaSonar3.csv",
                        on_click=lambda e: read_measurements("LeituraSubidaSonar3.csv", page, table, ax, line_1, line_2)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.ElevatedButton(
                        text="Ler Descida 1", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraDescidaSonar1.csv",
                        on_click=lambda e: read_measurements("LeituraDescidaSonar1.csv", page, table, ax, line_1, line_2)
                    ),
                    ft.ElevatedButton(
                        text="Ler Descida 2", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraDescidaSonar2.csv",
                        on_click=lambda e: read_measurements("LeituraDescidaSonar2.csv", page, table, ax, line_1, line_2)
                    ),
                    ft.ElevatedButton(
                        text="Ler Descida 3", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraDescidaSonar3.csv",
                        on_click=lambda e: read_measurements("LeituraDescidaSonar3.csv", page, table, ax, line_1, line_2)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.ElevatedButton(
                        text="Sair", icon=ft.Icons.EXIT_TO_APP, width=200,
                        tooltip="Sair do Programa",
                        on_click=lambda e: page.window.close()
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
    )

    # Adicionando os elementos à página
    page.add(
        ft.Column([
            distance_text,
            bar_a5,
            ft.Row([
                table_container,  # Container da tabela
                graph_container,  # Container com o gráfico
            ], alignment=ft.MainAxisAlignment.START),
            buttons_container
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

    

    try:
        board = telemetrix.Telemetrix()
        perform_readings(board, TRIGGER_PIN, ECHO_PIN)
        
        while True:
            update_distance(page, bar_a5, bar_a5_value, distance_text)
            await asyncio.sleep(1.0)
    finally:
        board.shutdown()

ft.app(target=main)
