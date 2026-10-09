import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock

Window.clearcolor = (0.12, 0.12, 0.16, 1)

SHAPES = [
    [(0,0)],  # Точка (1х1)
    [(0,0), (1,0)],  # Линия гориз (2х1)
    [(0,0), (0,1)],  # Линия верт (1х2)
    [(0,0), (1,0), (0,1)],  # Уголок (L)
    [(0,0), (1,0), (2,0)],  # Длинная линия (3х1)
    [(0,0), (1,0), (0,1), (1,1)]  # Квадрат (2х2)
]

SHAPE_COLORS = [
    (0.9, 0.2, 0.2), (0.2, 0.8, 0.2), (0.2, 0.5, 0.9),
    (0.9, 0.7, 0.1), (0.6, 0.2, 0.8), (0.1, 0.8, 0.8)
]

class Particle:
    """Класс для отдельной песчинки эффекта разрушения"""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        # Случайное направление разлета трухи
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(2, 7)
        self.alpha = 1.0  # Прозрачность
        self.size = random.uniform(4, 8)  # Размер песчинки

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy -= 0.3  # Гравитация тянет труху вниз
        self.alpha -= 0.04  # Плавное растворение
        return self.alpha > 0

class BlockBlastGame(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.grid_size = 8
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.score = 0
        self.game_over = False
        
        self.next_shape_idx = random.randint(0, len(SHAPES) - 1)
        self.is_dragging = False
        self.drag_x = 0
        self.drag_y = 0
        
        # Список для хранения активных частиц анимации
        self.particles = []
        
        self.score_label = Label(
            text=f"СЧЕТ: {self.score}", font_size='28sp', bold=True,
            pos=(20, Window.height - 80), size_hint=(None, None)
        )
        self.add_widget(self.score_label)
        
        self.hint_label = Label(
            text="Перетащи блок на поле!", font_size='16sp',
            pos=(0, 30), size_hint=(Window.width, None), color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(self.hint_label)

        self.bind(pos=self.draw_everything, size=self.draw_everything)
        
        # Запускаем постоянное обновление анимации частиц (60 FPS)
        Clock.schedule_interval(self.update_particles, 1/60.0)

    def calculate_sizes(self):
        self.cell_size = min(Window.width, Window.height) * 0.8 / self.grid_size
        self.grid_width = self.cell_size * self.grid_size
        self.start_x = (Window.width - self.grid_width) / 2
        self.start_y = (Window.height - self.grid_width) / 2 + 80
        
        self.preview_cell = self.cell_size * 0.8
        self.preview_center_x = Window.width / 2 - self.preview_cell
        self.preview_center_y = self.start_y - 140

    def update_particles(self, dt):
        """Регулярное обновление состояния всех песчинок"""
        # Обновляем каждую частицу и удаляем те, которые уже испарились
        self.particles = [p for p in self.particles if p.update()]
        # Вызываем перерисовку экрана для анимации
        self.draw_everything()

    def spawn_dust(self, row, col, color):
        """Создает облако трухи на месте уничтоженного кубика"""
        x = self.start_x + col * self.cell_size + self.cell_size / 2
        y = self.start_y + row * self.cell_size + self.cell_size / 2
        # Создаем 12 песчинок для каждого сгоревшего блока
        for _ in range(12):
            self.particles.append(Particle(x, y, color))

    def draw_everything(self, *args):
        self.canvas.before.clear()
        self.canvas.clear()
        self.calculate_sizes()
        
        with self.canvas.before:
            # Подложка поля
            Color(0.18, 0.18, 0.24, 1)
            Rectangle(pos=(self.start_x - 10, self.start_y - 10), 
                      size=(self.grid_width + 20, self.grid_width + 20))
            
            # Рендеринг сетки
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    x = self.start_x + col * self.cell_size
                    y = self.start_y + row * self.cell_size
                    
                    if self.grid[row][col] != 0:
                        Color(*self.grid[row][col], 1)
                    else:
                        Color(0.25, 0.25, 0.32, 1)
                    Rectangle(pos=(x + 2, y + 2), size=(self.cell_size - 4, self.cell_size - 4))
        
        # Рендеринг летающей трухи (эффект разрушения)
        with self.canvas:
            for p in self.particles:
                Color(p.color[0], p.color[1], p.color[2], p.alpha)
                Rectangle(pos=(p.x, p.y), size=(p.size, p.size))

        # Рендеринг перетаскиваемого блока
        shape = SHAPES[self.next_shape_idx]
        color = SHAPE_COLORS[self.next_shape_idx]
        
        with self.canvas:
            Color(*color, 1)
            if self.is_dragging:
                for dx, dy in shape:
                    px = self.drag_x + dx * self.cell_size
                    py = self.drag_y + dy * self.cell_size
                    Rectangle(pos=(px, py), size=(self.cell_size - 4, self.cell_size - 4))
            else:
                for dx, dy in shape:
                    px = self.preview_center_x + dx * self.preview_cell
                    py = self.preview_center_y + dy * self.preview_cell
                    Rectangle(pos=(px, py), size=(self.preview_cell - 2, self.preview_cell - 2))

    def on_touch_down(self, touch):
        if self.game_over:
            return super().on_touch_down(touch)
            
        min_x = self.preview_center_x - 20
        max_x = self.preview_center_x + self.preview_cell * 3 + 20
        min_y = self.preview_center_y - 20
        max_y = self.preview_center_y + self.preview_cell * 3 + 20
        
        if min_x <= touch.x <= max_x and min_y <= touch.y <= max_y:
            self.is_dragging = True
            self.drag_x = touch.x - self.cell_size / 2
            self.drag_y = touch.y - self.cell_size / 2
            self.draw_everything()
            return True
            
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.is_dragging:
            self.drag_x = touch.x - self.cell_size / 2
            self.drag_y = touch.y - self.cell_size / 2
            self.draw_everything()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.is_dragging:
            self.is_dragging = False
            
            if (self.start_x <= touch.x <= self.start_x + self.grid_width and 
                self.start_y <= touch.y <= self.start_y + self.grid_width):
                
                col = int((self.drag_x - self.start_x + self.cell_size / 2) // self.cell_size)
                row = int((self.drag_y - self.start_y + self.cell_size / 2) // self.cell_size)
                
                if self.place_shape(row, col):
                    self.check_lines()
                    self.next_shape_idx = random.randint(0, len(SHAPES) - 1)
                    
                    filled = sum(1 for r in self.grid for c in r if c != 0)
                    if filled > (self.grid_size * self.grid_size * 0.8):
                        self.trigger_game_over()
            
            self.draw_everything()
            return True
            
        return super().on_touch_up(touch)

    def place_shape(self, row, col):
        shape = SHAPES[self.next_shape_idx]
        color = SHAPE_COLORS[self.next_shape_idx]
        
        for dx, dy in shape:
            r = row + dy
            c = col + dx
            if not (0 <= r < self.grid_size and 0 <= c < self.grid_size) or self.grid[r][c] != 0:
                return False
                
        for dx, dy in shape:
            self.grid[row + dy][col + dx] = color
        return True

    def check_lines(self):
        rows_to_clear = []
        cols_to_clear = []
        
        for r in range(self.grid_size):
            if all(cell != 0 for cell in self.grid[r]):
                rows_to_clear.append(r)
                
        for c in range(self.grid_size):
            if all(self.grid[r][c] != 0 for r in range(self.grid_size)):
                cols_to_clear.append(c)
                
        # Генерируем труху перед тем, как стереть данные блоков
        for r in rows_to_clear:
            for c in range(self.grid_size):
                if self.grid[r][c] != 0:
                    self.spawn_dust(r, c, self.grid[r][c])
                    
        for c in cols_to_clear:
            for r in range(self.grid_size):
                # Избегаем повторного спавна, если ячейка уже очищена строкой
                if self.grid[r][c] != 0: 
                    self.spawn_dust(r, c, self.grid[r][c])

        # Очищаем ячейки в логике
        for r in rows_to_clear:
            self.grid[r] = [0 for _ in range(self.grid_size)]
            self.score += 100
            
        for c in cols_to_clear:
            for r in range(self.grid_size):
                self.grid[r][c] = 0
            self.score += 100
            
        if rows_to_clear or cols_to_clear:
            self.score_label.text = f"СЧЕТ: {self.score}"

    def trigger_game_over(self):
        self.game_over = True
        self.hint_label.text = "МЕСТА НЕТ! Игра окончена."
        self.hint_label.color = (1, 0, 0, 1)

class BlockBlastApp(App):
    def build(self):
        return BlockBlastGame()

if __name__ == '__main__':
    BlockBlastApp().run()
