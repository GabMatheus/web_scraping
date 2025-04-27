import sys
import requests
from datetime import datetime
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QTableWidget, \
    QTableWidgetItem, QHeaderView, QFileDialog
from PyQt5.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cotação de Moedas e Criptos")

        # Layout principal
        self.layout = QVBoxLayout()

        # Layout para os botões
        self.layout_buttons = QHBoxLayout()

        self.botao_atualizar = QPushButton("Ver Preços na Última Atualização")
        self.botao_atualizar.clicked.connect(self.atualizar_cotacoes)
        self.layout_buttons.addWidget(self.botao_atualizar)

        self.botao_salvar = QPushButton("Salvar em CSV")
        self.botao_salvar.clicked.connect(self.salvar_csv)
        self.layout_buttons.addWidget(self.botao_salvar)

        self.botao_grafico = QPushButton("Ver Gráfico de Comparação")
        self.botao_grafico.clicked.connect(self.gerar_grafico)
        self.layout_buttons.addWidget(self.botao_grafico)

        self.layout.addLayout(self.layout_buttons)

        # Tabela para exibir as cotações
        self.preco_table = QTableWidget()
        self.preco_table.setRowCount(0)
        self.preco_table.setColumnCount(3)
        self.preco_table.setHorizontalHeaderLabels(['Moeda/Cripto', 'Preço (R$)', 'Última Atualização'])
        self.preco_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preco_table.setAlternatingRowColors(True)
        self.preco_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.preco_table)

        # Canvas para o gráfico
        self.canvas = FigureCanvas(plt.figure())
        self.layout.addWidget(self.canvas)

        # Container
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.cotacoes = {}

    def atualizar_cotacoes(self):
        # Limpa a tabela antes de tentar atualizar
        self.preco_table.setRowCount(0)

        try:
            # URLs para as cotações
            url_moedas = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL,JPY-BRL,CAD-BRL,AUD-BRL,CHF-BRL"
            url_criptos = "https://economia.awesomeapi.com.br/last/BTC-BRL,ETH-BRL"

            # Requisições com tratamento de erro
            cotacoes = self.obter_dados(url_moedas, url_criptos)
            if not cotacoes:
                return

            self.cotacoes = cotacoes
            self.mostrar_precos()

        except Exception as e:
            self.mostrar_erro(f"Ocorreu um erro inesperado: {str(e)}")

    def obter_dados(self, url_moedas, url_criptos):
        """Função para obter dados de moedas e criptos."""
        cotacoes = {}

        try:
            resposta_moedas = requests.get(url_moedas, timeout=10)
            resposta_moedas.raise_for_status()
            resposta_criptos = requests.get(url_criptos, timeout=10)
            resposta_criptos.raise_for_status()

            dados_moedas = resposta_moedas.json()
            dados_criptos = resposta_criptos.json()

            # Combina dados de moedas e criptos
            cotacoes = {**dados_moedas, **dados_criptos}
            return cotacoes

        except requests.exceptions.RequestException as e:
            self.mostrar_erro(f"Erro ao buscar dados: {str(e)}")
            return {}

        except ValueError as e:
            self.mostrar_erro(f"Erro ao processar os dados da API: {str(e)}")
            return {}

    def mostrar_erro(self, mensagem):
        """Exibe uma mensagem de erro na tabela."""
        self.preco_table.setRowCount(1)
        self.preco_table.setItem(0, 0, QTableWidgetItem("Erro"))
        self.preco_table.setItem(0, 1, QTableWidgetItem(mensagem))
        self.preco_table.setItem(0, 2, QTableWidgetItem(""))

        for col in range(3):
            item = self.preco_table.item(0, col)
            if item:
                item.setTextAlignment(Qt.AlignCenter)
        print(mensagem)  # Log do erro no console

    def mostrar_precos(self):
        """Exibe as cotações na tabela."""
        self.preco_table.setRowCount(0)

        for row, (codigo, info) in enumerate(self.cotacoes.items()):
            try:
                self.preco_table.insertRow(row)

                nome = info['name'].replace("Real Brasileiro", "Real")  # Ajuste no nome
                preco = float(info['bid'])
                data_original = info['create_date']
                data_obj = datetime.strptime(data_original, "%Y-%m-%d %H:%M:%S")
                data_formatada = data_obj.strftime("%d/%m/%Y às %H:%M")

                self.preco_table.setItem(row, 0, QTableWidgetItem(nome))
                self.preco_table.setItem(row, 1, QTableWidgetItem(f"R$ {preco:,.2f}"))
                self.preco_table.setItem(row, 2, QTableWidgetItem(data_formatada))

                for col in range(3):
                    item = self.preco_table.item(row, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            except (ValueError, KeyError) as e:
                print(f"Erro ao processar {codigo}: {str(e)}")
                continue

    def salvar_csv(self):
        """Salva os dados das cotações em um arquivo CSV."""
        if not self.cotacoes:
            print("Nenhum dado para salvar!")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv);;All Files (*)")

        if not file_path:
            print("Salvamento cancelado pelo usuário.")
            return

        with open(file_path, mode='w', newline='', encoding='utf-8-sig') as arquivo_csv:
            escritor = csv.writer(arquivo_csv)
            escritor.writerow(['Nome', 'Código', 'Preço (R$)', 'Data e Hora'])

            for codigo, info in self.cotacoes.items():
                nome = info['name'].replace("Real Brasileiro", "Real")  # Ajuste no nome
                preco = float(info['bid'])
                data = datetime.strptime(info['create_date'], "%Y-%m-%d %H:%M:%S")
                data_formatada = data.strftime("%d/%m/%Y às %H:%M")
                escritor.writerow([nome, codigo, f"{preco:.2f}", data_formatada])

        print(f"Dados salvos em '{file_path}'")

    def gerar_grafico(self):
        """Gera um gráfico de pizza com os preços das moedas e criptos."""
        if not self.cotacoes:
            print("Nenhum dado para gerar gráfico!")
            return

        # Separar moedas comuns e criptos
        moedas_comuns = {k: v for k, v in self.cotacoes.items() if
                         k in ['USDBRL', 'EURBRL', 'GBPBRL', 'JPYBRL', 'CADBRL', 'AUDBRL', 'CHFBRL']}
        criptos = {k: v for k, v in self.cotacoes.items() if k in ['BTCBRL', 'ETHBRL']}

        # Preparar dados para os gráficos
        nomes_moedas = [info['name'].replace("Real Brasileiro", "Real") for info in
                        moedas_comuns.values()]  # Ajuste no nome
        precos_moedas = [float(info['bid']) for info in moedas_comuns.values()]
        nomes_criptos = [info['name'] for info in criptos.values()]
        precos_criptos = [float(info['bid']) for info in criptos.values()]

        self.plotar_grafico_pizza(nomes_moedas, precos_moedas, nomes_criptos, precos_criptos)

    def plotar_grafico_pizza(self, nomes_moedas, precos_moedas, nomes_criptos, precos_criptos):
        """Plota dois gráficos de pizza lado a lado."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), facecolor='#f5f5f5')

        def autopct_format(values):
            """Função para exibir valores formatados como moeda no gráfico de pizza."""

            def my_format(pct):
                total = sum(values)
                val = (pct * total) / 100.0
                return f'R$ {val:,.2f}'

            return my_format

        # Gráfico de pizza para moedas comuns
        ax1.pie(precos_moedas, labels=nomes_moedas, autopct=autopct_format(precos_moedas), startangle=90,
                colors=plt.cm.Paired(range(len(nomes_moedas))))
        ax1.set_title('Real', fontsize=14, fontweight='bold', fontfamily='Arial')
        ax1.axis('equal')

        # Gráfico de pizza para criptos
        ax2.pie(precos_criptos, labels=nomes_criptos, autopct=autopct_format(precos_criptos), startangle=90,
                colors=plt.cm.Paired(range(len(nomes_criptos))))
        ax2.set_title('Criptomoedas', fontsize=14, fontweight='bold', fontfamily='Arial')
        ax2.axis('equal')

        # Ajuste de layout
        plt.tight_layout()
        self.canvas.figure = fig
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

