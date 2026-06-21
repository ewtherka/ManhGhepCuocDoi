import pygame
import sys
import minigame

def preview():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Preview Slot Machine")
    clock = pygame.time.Clock()

    machine = minigame.SlotMachine(screen, clock)
    result = machine.run()
    
    print(f"\n=> Kết quả bạn quay được: {result}\n")
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    preview()
