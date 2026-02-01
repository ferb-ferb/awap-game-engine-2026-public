
import random
from collections import deque
from typing import Tuple, Optional, List

from game_constants import Team, TileType, FoodType, ShopCosts
from robot_controller import RobotController
from item import Pan, Plate, Food
class BotPlayer:
    def __init__(self,map_copy):
        self.map = map_copy
        self.bot0 = None
        self.b0state = 0 
        self.b1state = 0 
        self.bot1 = None
    
    def get_bfs_path(self, controller: RobotController, start: Tuple[int, int], target_predicate,blocked: Optional[Tuple[int,int]] = None) -> Optional[Tuple[int, int]]:
        queue = deque([(start, [])]) 
        visited = set([start])
        w, h = self.map.width, self.map.height

        while queue:
            (curr_x, curr_y), path = queue.popleft()
            tile = controller.get_tile(controller.get_team(), curr_x, curr_y)
            if target_predicate(curr_x, curr_y, tile):
                if not path: return (0, 0) 
                return path[0] 

            for dx in [0, -1, 1]:
                for dy in [0, -1, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = curr_x + dx, curr_y + dy
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                        if blocked and (nx, ny) == blocked:  # <-- avoid other bot
                            continue
                        if controller.get_map().is_tile_walkable(nx, ny):
                            visited.add((nx, ny))
                            queue.append(((nx, ny), path + [(dx, dy)]))
        return None

    def move_towards(self, controller: RobotController, bot_id: int, target_x: int, target_y: int, other_pos: Tuple[int,int]) -> bool:
        bot_state = controller.get_bot_state(bot_id)
        bx, by = bot_state['x'], bot_state['y']
        def is_adjacent_to_target(x, y, tile):
            return max(abs(x - target_x), abs(y - target_y)) <= 1
        if is_adjacent_to_target(bx, by, None): return True
        step = self.get_bfs_path(controller, (bx, by), is_adjacent_to_target, other_pos)
        if step and (step[0] != 0 or step[1] != 0):
            controller.move(bot_id, step[0], step[1])
            return False 
        return False 

    def find_nearest_tile(self, controller: RobotController, bot_x: int, bot_y: int, tile_name: str) -> Optional[Tuple[int, int]]:
        best_dist = 9999
        best_pos = None
        m = controller.get_map()
        for x in range(m.width):
            for y in range(m.height):
                tile = m.tiles[x][y]
                if tile.tile_name == tile_name:
                    dist = max(abs(bot_x - x), abs(bot_y - y))
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = (x, y)
        return best_pos
    
    def goto_loc(self,bot: str, controller: RobotController, b0x: int, b0y: int, title: str , other_pos: Tuple[int,int])-> Optional[Tuple[int, int]]:
        loc_pos = self.find_nearest_tile(controller, b0x, b0y,title) 
        lx, ly = loc_pos
        if self.move_towards(controller,getattr(self,bot), lx, ly, other_pos): 
            return (lx,ly)
        else: return None

    def buy_next(self,bot: str, controller: RobotController, bx: int, by: int, other_pos: Tuple[int,int]) -> Optional[str]:
        foods_list = self.orders[0]['required']
        shoploc = self.goto_loc(bot, controller, bx, by, "SHOP",other_pos)
        if shoploc == None:
            return None
        else:
            sx,sy = shoploc
            controller.buy(getattr(self,bot),getattr(FoodType,foods_list[0]) , sx,sy) 
            return foods_list[0]

    def buy_plate(self,bot: str, controller: RobotController, b0x: int, b0y: int, other_pos: Tuple[int,int]) -> bool:
        shoploc = self.goto_loc(bot, controller, b0x, b0y, "SHOP",other_pos)
        if shoploc == None:
            return False
        else:
            sx,sy = shoploc
            controller.buy(getattr(self,bot),ShopCosts.PLATE , sx,sy) 
            return True

    def place_counter(self,bot: str, controller: RobotController, b0x: int, b0y: int,other_pos: Tuple[int,int]) -> bool:
        placeloc = self.goto_loc(bot,controller, b0x, b0y, "COUNTER", other_pos)
        if placeloc == None:
            return False
        else:
            cx,cy = placeloc
            if not controller.place(getattr(self,bot),cx,cy):
                #controller.add_food_to_plate(getattr(self,bot),cx,cy)
                if bot == "bot0":
                    #controller.place(getattr(self,bot),b0x,b0y)
                    self.b0state = 69
                    return True
                elif bot == "bot1":
                    self.b1state = 420 
                    return True

            else: return True

    def play_turn(self, controller: RobotController):
        mybots = controller.get_team_bot_ids()
        self.orders = controller.get_orders()
        if not mybots: return

        self.bot0 = mybots[0]
        self.bot1 = mybots[1]
        
        b0info = controller.get_bot_state(self.bot0)
        b1info = controller.get_bot_state(self.bot1)
        b0x, b0y = b0info['x'], b0info['y']
        b1x, b1y = b1info['x'], b1info['y']
        
        if self.b0state == 0:
            if self.buy_plate("bot0",controller, b0x, b0y,(b1x,b1y)):
                self.b0state = 1 
            else: pass
        elif self.b0state == 1:
            if self.place_counter("bot0",controller, b0x, b0y,(b1x,b1y)):
                print(self.b0state)
                if self.b0state == 1: 
                    self.b0state = 3
                else: pass 
            else: pass 

        elif self.b0state == 3:
            print("done")

        #blocked counter handler bot 0
        elif self.b0state == 69:
            print("doing this")
            coords = self.find_nearest_tile(controller, b0x,b0y, "COUNTER")
            cx, cy = coords 
            didit = controller.add_food_to_plate(self.bot0,cx,cy)
            print(didit)
            self.b0state = 70
        elif self.b0state == 70:
            print("doingthis")
            controller.place(self.bot0,b0x,b0y)
            self.b0state = 3






        if self.b1state == 0:
            item = self.buy_next("bot1",controller, b1x,b1y,(b0x,b0y))
            if not item == None:
                if item == "NOODLES":
                    print("got some noodles niha")
                elif item == "MEAT":
                    print("got some meat boi")
                self.b1state = 1
            else: pass
        #elif self.b1state == 1:
         #   c_loc = self.goto_loc("bot1", controller, b1x,b1y,"COUNTER")
          #  if c_loc == None:
           #     pass
            #else:
             #   self.b1state == 2
        elif self.b1state == 1:
            if self.place_counter("bot1", controller, b1x,b1y,(b0x,b0y)):
                if self.b1state == 1: 
                    self.b1state = 0
                else: pass 
            else: 
                pass

        #blocked counter handler bot 1
        elif self.b1state == 420:
            coords = self.find_nearest_tile(controller, b0x,b0y, "COUNTER")
            cx, cy = coords
            controller.add_food_to_plate(self.bot1,cx,cy)
            self.b1state = 0

        elif self.b1state == 2:
            b1_shop_loc = self.goto_loc("bot1", controller, b1x,b1y,"SHOP", (b0x,b0y))
            if b1_shop_loc == None:
                pass
            else: 
                pass 

        return
        


        
        

        

        
