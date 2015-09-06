#! /usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright (C) 2013 and 2015 Tim Radvan and Ethan Smith
#    This file is part of SKIPY.
#
#    SKIPY is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    SKIPY is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with SKIPY.  If not, see <http://www.gnu.org/licenses/>.


import pygame
from pygame.locals import *
import skip
from skip import *
import kurt
from pygame import draw
from pygame import Rect as rect
import time


class MainWindow(skip.Screen):
    def __init__(self):
        pygame.init()
        self._running = True
        self.size=1600,900
        self.CAPTION="SKIPY"
        self.KEYS_BY_NAME = {}
        self.screen = pygame.display.set_mode(self.size,pygame.RESIZABLE)
        pygame.display.set_caption(self.CAPTION)
        #setup gray background
        self.background=pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((243,244,245))
        self.background_rect=self.background.get_rect()
        #load images
        self.SpritesAndStage=pygame.image.load("SpritesAndStage.PNG")
        self.def_sprite=pygame.image.load("Default.png")
        self.choose_sprite=pygame.image.load("Choose_Hover.png")
        self.draw_sprite_rect=rect(385,self.screen.get_size()[1]-475, 23,23)
        self.error_img=pygame.image.load("Error.png")
        self.start=pygame.image.load("start.png")
        self.start_rect=Rect(0,0,30,30)
        self.error_layer=pygame.Surface((480,360),pygame.SRCALPHA)
        self.error_layer.blit(self.error_img,(0,0))
        self.error=False
        pygame.display.set_caption(self.CAPTION)
        self.clock = pygame.time.Clock()


        for constant in dir(pygame):
            if constant.startswith("K_"):
                key = eval("pygame."+constant)
                name = pygame.key.name(key)
                self.KEYS_BY_NAME[name] = key
        self.project = kurt.Project()
        self.sprite = kurt.Sprite(self.project, "Sprite1")
        self.sprite.costume = kurt.Costume("square",
                                      kurt.Image.new((60, 60), (0, 0, 0)))
        self.project.sprites = [self.sprite]
        self.project.convert("scratch14")
        self.surface=pygame.Surface((480,380),pygame.SRCALPHA)
        try:
            self.set_project(kurt.Project.load("default.sb"))
        except Exception as e:
            print("Error "+str(e))
        self.tick()


    def render(self):

        #titlebar
        draw.rect(self.background,(156,158,162),rect(0,0,1600,30))


        self.screen.blit(self.background, (0, 0))
        if self.screen.get_size()[1]<900:
            #too small, cut off image
            self.screen.blit(self.SpritesAndStage,(10,410))
            self.set_sprite_chooser()
        else:
            #big, resize accordingly
            self.screen.blit(self.SpritesAndStage,(10,(self.screen.get_size())[1]-490))
            self.set_sprite_chooser()
        #start
        self.screen.blit(self.start, (0,0))
        #stage
        self.screen.blit(self.surface, (10,30))
        if self.error:
            self.screen.blit(self.error_layer, (300,self.screen.get_size()[1]-490))
            time.sleep(2)
        pygame.display.flip()
    def set_sprite_chooser(self):
        #coordinates are (x,y,w,h): (385,y, 95,23)
        #if mouse in rect,
        if self.draw_sprite_rect.collidepoint(self.mouse_pos[0],self.mouse_pos[1]):
            self.screen.blit(self.choose_sprite,(386, self.screen.get_size()[1]-484))
        else:
            self.screen.blit(self.def_sprite,(385, self.screen.get_size()[1]-485))

    def cleanup(self):
        pygame.quit()


    def clear(self):
        self.pen_surface.fill((0,0,0,0))
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:

                name = pygame.key.name(event.key)
                if name in kurt.Insert(None, "key").options():
                    yield ScreenEvent("key_pressed", name)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.start_rect.collide_point((self.mouse_pos[0],self.mouse_pos[1])):
                        self.interpreter.start()
                        print("starting interpreter")
                    yield ScreenEvent("mouse_down")
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    yield ScreenEvent("mouse_up")

            elif event.type==VIDEORESIZE:
                self.screen=pygame.display.set_mode(event.dict['size'],pygame.RESIZABLE)
                self.screen.blit(pygame.transform.scale(self.background,event.dict['size']),(0,0))
            if event.type== MOUSEBUTTONDOWN and self.draw_sprite_rect.collidepoint(self.mouse_pos[0],self.mouse_pos[1]):
                self.error=True
            if event.type== MOUSEBUTTONDOWN and not self.draw_sprite_rect.collidepoint(self.mouse_pos[0],self.mouse_pos[1]):
                self.error=False

    def tick(self):
        self.clock.tick(40)
        self.mouse_pos=pygame.mouse.get_pos()
        self.render()
        events = list(self.handle_events())
        #GUI events
        for event in self.interpreter.tick(events):
            if event.kind == "clear":
                self.clear()
            elif event.kind == "stamp":
                self.stamp(event.scriptable)
            elif event.kind in ("say", "think"):
                print "::", unicode(event)
            else:
                print "::", event

        self.draw_sprite(self.project.stage, self.surface)
        self.surface.blit(self.pen_surface, (0, 0))
        for actor in self.project.actors:
            if isinstance(actor, kurt.Scriptable):
                if actor.is_visible:
                    self.draw_sprite(actor, self.surface)

        pygame.display.flip()

    def get_sprite_mask(self, sprite, color=None):
        if (sprite.direction != 0 and sprite.size != 1) or color is not None:
            surface = self.surfaces[sprite.costume.image]
            #if sprite.direction != 90 and sprite.size != 100:
            angle = -(sprite.direction - 90)
            scale = sprite.size / 100.0
            surface = pygame.transform.rotozoom(surface, angle, scale)
            if color is None:
                return pygame.mask.from_surface(surface)
            else:
                return color_mask(surface, color)
        else:
            return self.masks[sprite.costume.image]

    def draw_sprite(self, sprite, onto_surface, offset=None):
        surface = self.surfaces[sprite.costume.image]
        if isinstance(sprite, kurt.Stage):
            pos = (0, 0)
        else:
            pos = self.pos_to_screen(skip.bounds(sprite).topleft)
            #if sprite.direction != 90 and sprite.size != 100:
            angle = -(sprite.direction - 90)
            scale = sprite.size / 100.0
            surface = pygame.transform.rotozoom(surface, angle, scale)

        if offset:
            (ox, oy) = offset
            (x, y) = pos
            pos = (x + ox, y + oy)

        ghost = sprite.graphic_effects['ghost']
        if ghost != 0:
            opacity = (100 - abs(ghost)) * 2.55
            blit_alpha(onto_surface, surface, pos, opacity)
        else:
            onto_surface.blit(surface, pos)

    def pos_to_screen(self, (x, y)):
        return (int(x) + 240,  180 - int(y))

    def pos_from_screen(self, (x, y)):
        return (x - 240, 180 - y)

    def draw_stage_without_sprite(self, sprite):
        _rect = skip.bounds(sprite)
        (x, y) = self.pos_to_screen(rect.topleft)
        offset = (-x, -y)
        surface = pygame.Surface(_rect.size).convert_alpha()
        self.draw_sprite(self.project.stage, surface, offset)
        surface.blit(self.pen_surface, (0, 0))
        for actor in self.project.actors:
            if actor is not sprite:
                if isinstance(actor, kurt.Scriptable):
                    if actor.is_visible:
                        self.draw_sprite(actor, surface, offset)
        return surface
    def set_project(self, project):
        self.running = True

        self.pen_surface = pygame.Surface((480,360)).convert_alpha()
        self.clear()

        self.surfaces = {}
        self.masks = {}
        self.sounds = {}

        skip.Screen.set_project(self, project)
        if project.name:
            pygame.display.set_caption(project.name + " : " + self.CAPTION)
        else:
            pygame.display.set_caption(self.CAPTION)
        for scriptable in [project.stage] + project.sprites:
            for costume in scriptable.costumes:
                p_i = costume.image.pil_image
                assert p_i.mode in ("RGB", "RGBA")
                surface = pygame.image.fromstring(
                        p_i.tostring(), p_i.size, p_i.mode).convert_alpha()
                self.surfaces[costume.image] = surface
                self.masks[costume.image] = pygame.mask.from_surface(surface)


    def stamp(self, sprite):
        self.draw_sprite(sprite, self.pen_surface)

    # Script methods

    def draw_line(self, start, end, color, size):
        start = self.pos_to_screen(start)
        end = self.pos_to_screen(end)
        pygame.draw.line(self.pen_surface, color.value, start, end, size)

    def get_mouse_pos(self):
        return self.pos_from_screen(pygame.mouse.get_pos())

    def is_mouse_down(self):
        return pygame.mouse.get_pressed()[0]

    def is_key_pressed(self, name):
        if name.endswith(" arrow"):
            name = name[:-6]
        key = self.KEYS_BY_NAME[name]
        return pygame.key.get_pressed()[key]

    def touching_mouse(self, sprite):
        mask = self.get_sprite_mask(sprite)
        (x, y) = self.pos_to_screen(skip.bounds(sprite).topleft)
        (mx, my) = pygame.mouse.get_pos()
        return bool(mask.get_at((int(mx - x), int(my - y))))

    def touching_sprite(self, sprite, other):
        mask = self.get_sprite_mask(sprite)
        other_mask = self.get_sprite_mask(other)
        (x, y) = self.pos_to_screen(skip.bounds(sprite).topleft)
        (ox, oy) = self.pos_to_screen(skip.bounds(other).topleft)
        offset = (int(ox - x), int(oy - y))
        return bool(mask.overlap(other_mask, offset))

    def touching_color(self, sprite, color):
        rendered_surface = self.draw_stage_without_sprite(sprite)
        rendered_mask = color_mask(rendered_surface, color)
        sprite_mask = self.get_sprite_mask(sprite)
        return bool(rendered_mask.overlap(sprite_mask, (0, 0)))

    def touching_color_over(self, sprite, color, over):
        rendered_surface = self.draw_stage_without_sprite(sprite)
        rendered_mask = color_mask(rendered_surface, over)
        sprite_mask = self.get_sprite_mask(sprite, color)
        return bool(rendered_mask.overlap(sprite_mask, (0, 0)))

    def ask(self, scriptable, prompt):
        # sync: yield while waiting for answer.
        while 0: # TODO
            yield
        yield ""

    def play_sound(self, sound):
        pass # TODO

    def play_sound_until_done(self, sound):
        self.play_sound(sound)
        while 0: # sync: yield while playing
            yield

    def stop_sounds(self):
        pass # TODO

    def play_note(self, drum, duration):
        pass

    def play_drum(self, drum, duration):
        pass

if __name__=="__main__":
    app=MainWindow()
    #mainloop
    while app.running:
        app.tick()



