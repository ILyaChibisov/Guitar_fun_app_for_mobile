# utils/kivy_imports.py
"""
Совместимые импорты для KivyMD 2.0
"""
# Кнопки
try:
    from kivymd.uix.button import MDRaisedButton, MDIconButton
    from kivymd.uix.button import MDRectangleFlatButton as MDFlatButton
except ImportError:
    try:
        from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
    except ImportError:
        from kivy.uix.button import Button as MDRaisedButton
        from kivy.uix.button import Button as MDIconButton
        from kivy.uix.button import Button as MDFlatButton

# Snackbar
try:
    from kivymd.uix.snackbar import Snackbar
except ImportError:
    try:
        from kivymd.uix.snackbar import MDSnackbar as Snackbar
    except ImportError:
        from kivy.uix.label import Label as Snackbar

# Dialog
try:
    from kivymd.uix.dialog import MDDialog
except ImportError:
    from kivy.uix.popup import Popup as MDDialog

# Card
try:
    from kivymd.uix.card import MDCard
except ImportError:
    from kivy.uix.boxlayout import BoxLayout as MDCard

# Label
try:
    from kivymd.uix.label import MDLabel
except ImportError:
    from kivy.uix.label import Label as MDLabel

# TextField
try:
    from kivymd.uix.textfield import MDTextField
except ImportError:
    from kivy.uix.textinput import TextInput as MDTextField

# ProgressBar
try:
    from kivymd.uix.progressbar import MDProgressBar
except ImportError:
    from kivy.uix.progressbar import ProgressBar as MDProgressBar

# Screen
try:
    from kivymd.uix.screen import MDScreen
except ImportError:
    from kivy.uix.screenmanager import Screen as MDScreen

# BoxLayout
try:
    from kivymd.uix.boxlayout import MDBoxLayout
except ImportError:
    from kivy.uix.boxlayout import BoxLayout as MDBoxLayout

# ScrollView
try:
    from kivymd.uix.scrollview import MDScrollView
except ImportError:
    from kivy.uix.scrollview import ScrollView as MDScrollView

# Tabs
try:
    from kivymd.uix.tab import MDTabs, MDTabsBase
except ImportError:
    from kivy.uix.tabbedpanel import TabbedPanel as MDTabs
    from kivy.uix.tabbedpanel import TabbedPanelItem as MDTabsBase

# FloatLayout
try:
    from kivymd.uix.floatlayout import MDFloatLayout
except ImportError:
    from kivy.uix.floatlayout import FloatLayout as MDFloatLayout