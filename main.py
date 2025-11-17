import flet as ft
from ui.main_window import MainWindow


def main(page: ft.Page):
    app = MainWindow(page)
    app.initialize()


if __name__ == "__main__":
    ft.app(target=main)
