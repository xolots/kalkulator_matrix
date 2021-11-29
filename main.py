# All the import statements needed in current version or upcoming version
import kivy
from kivy.metrics import dp, sp
from kivy.properties import StringProperty, NumericProperty, OptionProperty, ColorProperty
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.behaviors import focus
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.utils import platform
from kivymd.app import MDApp
from kivy.utils import get_color_from_hex
from kivy.config import Config
from kivy.core.window import Window
import re
from fractions import Fraction

kivy.require('2.0.0')

# // Search for resources in project root file (optional)
Config.write()
kivy.resources.resource_add_path("./")


# // Sets status bar color to white on android
# // Currently, not working properly on modified ROMs like MIUI
def white_status_bar():
    from android.runnable import run_on_ui_thread  # type: ignore

    @run_on_ui_thread
    def _white_status_bar():
        from jnius import autoclass
        WindowManager = autoclass('android.view.WindowManager$LayoutParams')
        Color = autoclass('android.graphics.Color')
        activity = autoclass('org.kivy.android.PythonActivity').mActivity
        window = activity.getWindow()
        window.clearFlags(WindowManager.FLAG_TRANSLUCENT_STATUS)
        window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
        window.setStatusBarColor(Color.WHITE)
    _white_status_bar()


class MatrixValue(TextInput):
    def __init__(self, **kwargs):
        super(MatrixValue, self).__init__(**kwargs)
        self.background_normal = ''
        self.multiline = False
        self.write_tab = False
        self.padding_y = dp(self.width / 8)
        self.font_size = sp(20)
        self.background_color = [0, 0, 0, 0]

        self.cursor_color = (0, 0, 0, 0)
        self.fg_color = get_color_from_hex('#240E43')
        bg_color = get_color_from_hex('#13be8b')
        self.dummy_cursor_color = (0, 0, 0, 0)
        with self.canvas.before:
            Color(bg_color[0], bg_color[1], bg_color[2], bg_color[3])
            self.rounded_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6), ])
            Color(self.fg_color[0], self.fg_color[1], self.fg_color[2], self.fg_color[3])
        self.bind(pos=self.update_roundedbg, size=self.update_roundedbg, focus=self.cursor_visibility)

    def add_cursor(self, cursor_color):
        with self.canvas.after:
            self.canvas.after.clear()
            Color(cursor_color[0], cursor_color[1], cursor_color[2], cursor_color[3])
            self.dummy_cursor = Rectangle(pos=self.cursor_pos, size=(self.cursor_width * 2, -self.line_height))

        self.bind(cursor_pos=self.update_cursor_pos)

    def update_roundedbg(self, *args):
        self.rounded_bg.pos = self.pos
        self.rounded_bg.size = self.size

    def update_cursor_pos(self, *args):
        self.dummy_cursor.pos = self.cursor_pos

    def cursor_visibility(self, *args):
        self.add_cursor([1, 0, 0, 1] if self.focus else [0, 0, 0, 0])


# Development of grid layout that contains all the units of matrix
class MatrixGrid(GridLayout, BoxLayout):
    order = NumericProperty(0)

    # Function to make Matrix view as per the provided order
    def on_order(self, *args):

        order = int(self.order)
        try:
            MDApp.get_running_app().root.ids.display_box.text = ''
        except Exception:
            print("display_box belum dibuat.")
        self.clear_widgets()
        self.cols = order
        self.rows = order

        for i in range(1, order + 1):
            for k in range(1, order + 1):
                set_id = 'a' + str(i) + str(k)
                text_input = MatrixValue()
                text_input.id = set_id
                self.add_widget(text_input)


# // Our main App
# // All the initiations, exchanges and processes done here
class MatrixCalculator(MDApp):
    def __init__(self, **kwargs):
        self.title = "Kalkulator Matrix"

        super().__init__(**kwargs)

    # Convert input_matrix into nested lists
    def matrix_builder(self, values_list):
        Mvalues_list = []
        temp_list = []
        order = int(self.root.ids.input_matrix.order)

        for i in range(order):
            for k in range(order):
                temp_list.append(values_list[order * i + k])
            Mvalues_list.append(list(temp_list))
            temp_list.clear()

        return Mvalues_list

    # ////// Receive values of matrix units provided in grid layout
    def calculate(self):

        # // Receives all text boxes of Matrix Grid
        children_list = self.root.ids.input_matrix.children
        if not children_list:  # // Checks that calculation not done on empty set of values
            return "---"
        values_list = []  # // List of all valid values user entered
        error_list = []
        for child in children_list:  # // Checks and Fetches all units of matrix one-by-one
            error = Validator().chk_value(child.text)

            if error and error not in error_list:
                error_list.append(error)
            elif not error:
                values_list.append(Fraction(child.text).limit_denominator(999))  # Value converted to fraction
        else:  # After checking all values for validity
            if len(error_list) != 0:  # If error present
                if len(error_list) > 4:
                    error_list.insert(3, '. . .')  # Add 3 dots if more than 4 errors
                error_list = error_list[0:4]  # Display max. 4 errors at a time
                error_string = '\n'.join(error_list)
                self.root.ids.display_box.text = error_string
                return "---"
            else:  # If all values are complete and error free
                self.root.ids.display_box.text = ''  # Removes error message when all values verified

        # // Covert Linear List to Matrix-type Nested List
        values_list.reverse()
        matrix_list = self.matrix_builder(values_list)

        # // Passes the matrix to calculate Determinant
        answer = Calculator().determinant(matrix_list)

        # // Sets the answer to display_box
        self.root.ids.display_box.text = "[size=25sp]Determinan nya adalah:       [anchor='right']{answer}[/size]".format(answer=str(answer))

    # //// Sets the root of our window
    def build(self):
        if platform == "android":
            Window.softinput_mode = 'below_target'  # // Added to fix text-box hidden behind keyboard
            white_status_bar()
        else:
            Window.size = (450, 750)  # // Default size for desktop

        return MainWindow()


# Root layout of our app
class MainWindow(BoxLayout):
    pass


# ////// Class dedicated to calculating determinant of matrix
class Calculator:
    def determinant(self, A, total=0):
        # Section 1: store indices in list for row referencing

        indices = list(range(len(A)))

        # Section 2: when at 2x2 sub-matrices recursive calls end
        if len(A) == 2 and len(A[0]) == 2:
            val = A[0][0] * A[1][1] - A[1][0] * A[0][1]
            return val

        # Section 3: define sub-matrix for focus column and
        #      call this function
        for fc in indices:  # A) for each focus column, ...
            # find the sub-matrix ...
            As = list(A)  # B) make a copy, and ...
            As = As[1:]  # ... C) remove the first row
            height = len(As)  # D)

            for i in range(height):
                # E) for each remaining row of submatrix ...
                #     remove the focus column elements
                As[i] = As[i][0:fc] + As[i][fc + 1:]

            sign = (-1) ** (fc % 2)  # F)
            # G) pass sub-matrix recursively
            sub_det = Calculator().determinant(As)
            # H) total all returns from recursion
            total += sign * A[0][fc] * sub_det

        return total


# *****************************************************************************
# ////// Class dedicated to verify user inputs
class Validator:

    def chk_value(self, value):
        value = re.sub(r"\s", "", value)  # // Removes all types of whitespaces
        error = None

        master_pattern = re.compile(r"^((\+|\-)?\d{1,3}(([\.]\d{1,2})|([\/]\d{1,3}))?){1}$")

        # // Checks for standard pattern
        # // If false, then do some pre-tests to find exact problem
        if not re.match(master_pattern, value):
            if value == '':
                error = "! kolom tidak boleh kosong."
            elif re.search(r"[^\+\-\.\/0-9]", value):
                error = "! ada karakter tidak valid."
            elif len(re.findall(r"[\/]", value)) > 1:
                error = "! kelipatan \'/\' dalam nilai tunggal tidak diperbolehkan."
            elif re.search(r"[\/](\+|\-)", value):
                error = "! +/- bisa numerator, tidak denominator."
            elif re.match(r"^((\+|\-)?\d{1,3}([\.]\d)?[\/](\+|\-)?\d{1,3}([\.]\d)?)$", value):
                error = "! desimal dan pecahan tidak bisa digabungkan."
            elif re.search(r"\d{4,}", value):
                error = "! Max. 3 digits untuk bagian numerik."
            else:
                error = "! kesalahan struktur."

        # // Returns "None" for no errors
        # // Otherwise specified error statement
        return error


# /// Driver needed to self start the function ---- VROOM! VROOM!
if __name__ == "__main__":
    MatrixCalculator().run()
