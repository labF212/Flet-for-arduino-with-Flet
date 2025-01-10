import csv
import flet as ft
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart

# Função para ler medições de um ficheiro
def read_measurements(file_name, page, table, ax, line_1, line_2, header_text):
    try:
        with open(file_name, mode='r') as file:
            reader = csv.reader(file)
            header = next(reader)  # lê linha de cabeçalho (opcional)
            next(reader)  

            # Atualiza o texto com o cabeçalho
            header_text.value = " | ".join(header)
            page.update()

            ensaios, horas, dist_medidas, dist_reais = [], [], [], []

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


def sobre_e_ajuda(page):
    # Criando o pop-up (Dialog) com Markdown
    markdown_content = ft.Markdown(
        """
# Sobre e Ajuda
Bem-vindo ao programa de leitura de distâncias com sensores **HC-SR04**!

### Funcionalidades
- Leitura de ficheiros CSV com resultados de medições.
- Gráficos interativos das distâncias medidas.
- Tabela detalhada com os resultados.

### Autor
- **Nome:** Paulo Galvão
- **Versão:** 1.0
- **Contato:** [paulo.galvao@estsetubal.ips.pt](mailto:paulo.galvao@estsetubal.ips.pt)

### Como Utilizar
1. Clique num dos botões de leitura para carregar um ficheiro CSV.
2. Visualize os dados na tabela e no gráfico.
3. Para mais informações, consulte a documentação.

### Observações
- Este software foi desenvolvido para fins educacionais.
- Certifique-se de usar ficheiros no formato esperado.

---

        """,
        extension_set="gitHub",  # Estilo do Markdown
        selectable=True,         # Permite selecionar o texto
    )

    # Criando botões para os links
    link_buttons = ft.Row(
        controls=[
            ft.TextButton(
                text="Onde Encontrar o Programa",
                tooltip="Pressione para ir para a página web",
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(
                        decoration=ft.TextDecoration.UNDERLINE
                    )
                ),

                on_click=lambda e: page.launch_url("https://github.com/labF212/Gui-for-Python-Flet"),
            ),
            ft.TextButton(
                text="Documentação Completa do Flet",
                tooltip="Pressione para ir para a página web",
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(
                        decoration=ft.TextDecoration.UNDERLINE
                    )
                ),
                on_click=lambda e: page.launch_url("https://flet.dev/docs/"),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    dialog = ft.AlertDialog(
        content=ft.Column(
            controls=[
            markdown_content,
            link_buttons,
            ],
        ),
    actions=[
        ft.TextButton(
            "Fechar",
            on_click=lambda e: close_dialog(page, dialog)
        ),
    ],
    )

    # Adicionando o diálogo aos overlays da página
    if dialog not in page.overlay:
        page.overlay.append(dialog)
    dialog.open = True
    page.update()



def close_dialog(page, dialog):
    dialog.open = False
    page.update()

# Função principal do Flet
async def main(page: ft.Page):
    page.title = "Leitura HC-SR04 com Telemetrix e Flet"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.ALWAYS   
    
    # Texto para o cabeçalho
    header_text = ft.Text(value="", size=14, weight=ft.FontWeight.BOLD)

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
            controls=[header_text, table],
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
        width=600,
        height=600
    )

    # Criando o pop-up (Dialog)
    dialog = ft.AlertDialog(
        title=ft.Text("Título do Pop-Up"),
        content=ft.Text("Este é o conteúdo do pop-up."),
        actions=[
            ft.TextButton(
                "Fechar",
                on_click=lambda e: dialog.close()
            ),
        ],
    )



    # Botões para leitura de ficheiros
    buttons_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row([
                    ft.ElevatedButton(
                        text="Ler Subida 1", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraSubidaSonar1.csv",
                        on_click=lambda e: read_measurements("LeituraSubidaSonar1.csv", page, table, ax, line_1, line_2, header_text)
                    ),
                    ft.ElevatedButton(
                        text="Ler Subida 2", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraSubidaSonar2.csv",
                        on_click=lambda e: read_measurements("LeituraSubidaSonar2.csv", page, table, ax, line_1, line_2, header_text)
                    ),
                    ft.ElevatedButton(
                        text="Ler Subida 3", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraSubidaSonar3.csv",
                        on_click=lambda e: read_measurements("LeituraSubidaSonar3.csv", page, table, ax, line_1, line_2, header_text)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.ElevatedButton(
                        text="Ler Descida 1", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraDescidaSonar1.csv",
                        on_click=lambda e: read_measurements("LeituraDescidaSonar1.csv", page, table, ax, line_1, line_2, header_text)
                    ),
                    ft.ElevatedButton(
                        text="Ler Descida 2", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraDescidaSonar2.csv",
                        on_click=lambda e: read_measurements("LeituraDescidaSonar2.csv", page, table, ax, line_1, line_2, header_text)
                    ),
                    ft.ElevatedButton(
                        text="Ler Descida 3", icon=ft.Icons.UPLOAD_FILE, width=200,
                        tooltip="Ler o ficheiro LeituraDescidaSonar3.csv",
                        on_click=lambda e: read_measurements("LeituraDescidaSonar3.csv", page, table, ax, line_1, line_2, header_text)
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row([
                    ft.ElevatedButton(
                        text="Sair", icon=ft.Icons.EXIT_TO_APP, width=200,
                        tooltip="Sair do Programa",
                        on_click=lambda e: page.window.close()
                    ),
                                
                    ft.ElevatedButton(
                        text="Sobre", icon=ft.Icons.HELP, width=200,
                        tooltip="Sobre e Ajuda",
                        on_click=lambda e: sobre_e_ajuda(page)
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
            ft.Row([
                table_container,  # Container da tabela
                graph_container,  # Container com o gráfico
            ], alignment=ft.MainAxisAlignment.START),
            buttons_container
        ], alignment=ft.MainAxisAlignment.CENTER)
    )
 
ft.app(target=main)
