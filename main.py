from kivy.app import App
from kivy.uix.widget import Widget


class TheBrowserWidget(Widget):
    pass


class TheBrowser(App):
    def build(self):
        return TheBrowserWidget()


if __name__ == '__main__':
    TheBrowser().run()