from kivy.app import App
from kivy.uix.widget import Widget


class Browser(Widget):
    pass


class BrowserApp(App):
    def build(self):
        return Browser()

    def process(self): 
        text = self.root.ids.input.text 
        print(text) 
  


if __name__ == '__main__':
    BrowserApp().run()