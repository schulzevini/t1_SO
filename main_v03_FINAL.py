import pygame # type: ignore
import random
import threading
import time

# Inicialização do Pygame
pygame.init()

# Configurações da tela
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Cores
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Configurações iniciais
RAIO = 10
NUM_NAVES = 10
SPEED = 1
MAX_FOGUETES = 5
foguetes_disponiveis = MAX_FOGUETES

# Lista para armazenar os foguetes e naves
foguetes = []
naves = []
mutex = threading.Lock()

# Contador de naves
naves_no_solo = 0
naves_abatidas = 0

# Função para gerar uma posição única
def generate_unique_position(raio, screen_width):
    with mutex:
        while True:
            x = random.randint(raio, screen_width - raio)
            if all(abs(x - nave.x) > 2 * raio for nave in naves):
                break
    return x

# Classe para as naves
class Nave(threading.Thread):
    def __init__(self, x, y, speed, raio):
        super().__init__()
        self.x = x
        self.y = y
        self.speed = speed
        self.raio = raio
        self.active = True

    def run(self):
        global naves_no_solo
        while self.active and self.y - self.raio <= SCREEN_HEIGHT:
            with mutex: #trava para cada se mover independentemente e sem colisao
                self.y += self.speed
            pygame.time.wait(30)  # Delay to control the speed of movement
        if self.y - self.raio > SCREEN_HEIGHT:
            with mutex:
                naves_no_solo += 1
                self.active = False

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (self.x, self.y), self.raio)

class Foguete(threading.Thread):
    def __init__(self, x, y, dx, dy, speed=5):
        super().__init__()
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.ativo = True

    def run(self):
        global naves_abatidas
        #verifica se o foguete esta ativo e dentro da tela
        while self.ativo and 0 <= self.x <= SCREEN_WIDTH and 0 <= self.y <= SCREEN_HEIGHT:
            with mutex: #mutex para garantir que os foguetes se movam independentemente 
                #self.x e self.y sao incrementados com base na direcao e velocidade
                self.x += self.dx * self.speed
                self.y += self.dy *self.speed
            pygame.time.wait(30) #controlar a velocidade do movimento do foguete.
            with mutex: #operacao atomica
                for nave in naves:
                    #calcula distancia entre o foguete e a nave usando a fórmula da distância Euclidiana
                    #se a distância for menor que o raio da nave (RAIO), significa que houve uma colisão
                    if nave.active and ((self.x - nave.x) ** 2 + (self.y - nave.y) ** 2) ** 0.5 < RAIO:
                        nave.active = False
                        self.ativo = False
                        naves_abatidas += 1
                        break
    
    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (self.x, self.y), 5)

class Bateria:
    def __init__(self, x, y, foguetes):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 15
        self.mira_width = 10
        self.mira_height = 30
        self.color = BLUE
        self.mira_color = GREEN
        self.carregada = True
        self.foguetes = foguetes
        self.direcao_mira = (0, -1) #mira iniciada para cima

    def draw(self, screen):
        self.color = BLUE if self.carregada else RED
        pygame.draw.rect(screen, self.color, (self.x - self.width // 2, self.y - self.height, self.width, self.height))
        # Desenha a mira
        mira_x = self.x + self.direcao_mira[0] * 20
        mira_y = self.y + self.direcao_mira[1] * 20
        angle = 0
        if self.direcao_mira == (1, 0):
            angle = -90
        elif self.direcao_mira == (-1, 0):
            angle = 90
        elif self.direcao_mira == (1, -1):
            angle = -45
        elif self.direcao_mira == (-1, -1):
            angle = 45
        elif self.direcao_mira == (0, -1):
            angle = 0
        mira_surface = pygame.Surface((self.mira_width, self.mira_height), pygame.SRCALPHA)
        mira_surface.fill(self.mira_color)
        rotated_mira = pygame.transform.rotate(mira_surface, angle)
        screen.blit(rotated_mira, rotated_mira.get_rect(center=(mira_x, mira_y)))

    def recarregar(self):
        self.foguetes = MAX_FOGUETES
        self.carregada = True

    def mudar_direcao_mira(self, dx, dy):
        self.direcao_mira = (dx, dy)


# Criar e iniciar naves
def criar_naves_com_atraso():
    for _ in range(NUM_NAVES):
        x = generate_unique_position(RAIO, SCREEN_WIDTH)
        nave = Nave(x, 0, SPEED, RAIO)
        naves.append(nave)
        nave.start()
        time.sleep(2)


def exibir_resultado(screen, mensagem):
    fonte = pygame.font.Font(None, 74)
    texto = fonte.render(mensagem, True, WHITE)
    rect = texto.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    screen.blit(texto, rect)
    pygame.display.flip()
    pygame.time.wait(2000)

def desenhar_texto(screen, texto, tamanho, cor, x, y):
    fonte = pygame.font.Font(None, tamanho)
    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect()
    rect.midtop = (x, y)
    screen.blit(superficie, rect)

def escolher_dificuldade():
    while True:
        screen.fill(BLACK)
        desenhar_texto(screen, "Escolha a Dificuldade", 74, WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/4)
        desenhar_texto(screen, "1. Fácil", 50, WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50)
        desenhar_texto(screen, "2. Médio", 50, WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        desenhar_texto(screen, "3. Difícil", 50, WHITE, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return 'facil'
                if event.key == pygame.K_2:
                    return 'medio'
                if event.key == pygame.K_3:
                    return 'dificil'

def main():
    global foguetes_disponiveis, naves_no_solo, naves_abatidas, MAX_FOGUETES, NUM_NAVES, SPEED

    dificuldade = escolher_dificuldade()
    if not dificuldade:
        return

    if dificuldade == 'facil':
        MAX_FOGUETES = 10
        NUM_NAVES = 5
        SPEED = 1
    elif dificuldade == 'medio':
        MAX_FOGUETES = 7
        NUM_NAVES = 10
        SPEED = 2
    elif dificuldade == 'dificil':
        MAX_FOGUETES = 5
        NUM_NAVES = 15
        SPEED = 3

    foguetes_disponiveis = MAX_FOGUETES
    threading.Thread(target=criar_naves_com_atraso).start()
    bateria = Bateria(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30, MAX_FOGUETES)
    direcao_foguete = (0, -1)  # Padrão: reto
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    direcao_foguete = (-1, -1)  # Diagonal esquerda
                    bateria.mudar_direcao_mira(-1, -1)
                elif event.key == pygame.K_RIGHT:
                    direcao_foguete = (1, -1)  # Diagonal direita
                    bateria.mudar_direcao_mira(1, -1)
                elif event.key == pygame.K_UP:
                    direcao_foguete = (0, -1)  # Reto
                    bateria.mudar_direcao_mira(0, -1)
                elif event.key == pygame.K_a:
                    direcao_foguete = (-1, 0)  # Esquerda
                    bateria.mudar_direcao_mira(-1, 0)
                elif event.key == pygame.K_d:
                    direcao_foguete = (1, 0)  # Direita
                    bateria.mudar_direcao_mira(1, 0)
                elif event.key == pygame.K_SPACE:
                    with mutex:
                        if foguetes_disponiveis > 0:
                            foguete = Foguete(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30, *direcao_foguete)
                            foguetes.append(foguete)
                            foguete.start()
                            foguetes_disponiveis -= 1
                elif event.key == pygame.K_r:
                    if foguetes_disponiveis <= MAX_FOGUETES:
                        bateria.recarregar()
                        with mutex:
                            foguetes_disponiveis = MAX_FOGUETES

       
        # Preencher a tela com fundo preto
        screen.fill(BLACK)

        #desenha bateria
        bateria.draw(screen)
    
        #desenha textos
        desenhar_texto(screen, f'Foguetes: {foguetes_disponiveis} / {MAX_FOGUETES}', 36, WHITE, SCREEN_WIDTH - 185, 10)
        desenhar_texto(screen, f'Naves Abatidas: {naves_abatidas}', 36, WHITE, SCREEN_WIDTH - 185, 50)
        desenhar_texto(screen, f'Naves Pousaram: {naves_no_solo}', 36, WHITE, SCREEN_WIDTH - 180, 90)


        # Atualizar e desenhar as naves
        with mutex:
            naves_ativas = [nave for nave in naves if nave.active]
            for nave in naves_ativas:
                nave.draw(screen)

        # Atualizar e desenhar foguetes
        with mutex:
            foguetes_ativos = [foguete for foguete in foguetes if foguete.ativo]
            for foguete in foguetes_ativos:
                foguete.draw(screen)

        if naves_abatidas >= NUM_NAVES / 2:
            exibir_resultado(screen, 'VOCE VENCEU!')
            running = False
        elif naves_no_solo > NUM_NAVES / 2:
            exibir_resultado(screen, 'VOCE PERDEU!')
            running = False

        # Atualizar a tela
        pygame.display.flip()
        pygame.time.Clock().tick(60)

    # Encerrar o Pygame
    pygame.quit()

if __name__ == '__main__':
    main()




