import sys
import random
import pygame
from typing import List, Optional, Tuple


NAIPE = '♠'
VALOR_NOME = {
    1: 'A', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7',
    8: '8', 9: '9', 10: '10', 11: 'J', 12: 'Q', 13: 'K'
}

class Carta:
    def __init__(self, valor: int, naipe: str = NAIPE, virada_para_cima: bool = False):
        self.valor = valor
        self.naipe = naipe
        self.virada_para_cima = virada_para_cima

    def virar(self):
        self.virada_para_cima = True

    def __str__(self):
        return f"{VALOR_NOME[self.valor]}{self.naipe}" if self.virada_para_cima else "##"


class Pilha:
    def __init__(self):
        self.cartas: List[Carta] = []

    def esta_vazia(self) -> bool:
        return len(self.cartas) == 0

    def topo(self) -> Optional[Carta]:
        return self.cartas[-1] if self.cartas else None

    def push(self, cartas: List[Carta]):
        self.cartas.extend(cartas)

    def pop(self, n: int = 1) -> List[Carta]:
        if n <= 0 or n > len(self.cartas):
            raise ValueError("Quantidade inválida no pop.")
        ret = self.cartas[-n:]
        self.cartas = self.cartas[:-n]
        return ret

    # Aqui o código tá verificando qual o índice da carta do topo a ser virada
    def _indice_inicio_bloco_visivel(self) -> int:
        if self.esta_vazia() or not self.topo().virada_para_cima:
            return len(self.cartas)
        i = len(self.cartas) - 1
        while i >= 0 and self.cartas[i].virada_para_cima:
            i -= 1
        return i + 1

    #vira o restante das cartas
    def bloco_visivel(self) -> List[Carta]:
        i = self._indice_inicio_bloco_visivel()
        return self.cartas[i:] if i < len(self.cartas) else []

    def _sequencia_decrescente_mesmo_naipe(self, cartas: List[Carta]) -> bool:
        if not cartas:
            return False
        for i in range(len(cartas) - 1):
            a, b = cartas[i], cartas[i+1]
            if a.valor != b.valor + 1 or a.naipe != b.naipe:
                return False
        return True

    def pode_mover_bloco_para(self, qtd: int, destino: 'Pilha') -> bool:
        bloco = self.cartas[-qtd:] if qtd <= len(self.cartas) else []
        if not bloco or not all(c.virada_para_cima for c in bloco):
            return False
        if not self._sequencia_decrescente_mesmo_naipe(bloco):
            return False
        if destino.esta_vazia():
            return True
        topo_dest = destino.topo()
        base = bloco[0]
        return topo_dest.virada_para_cima and topo_dest.naipe == base.naipe and topo_dest.valor == base.valor + 1

    def mover_bloco_para(self, qtd: int, destino: 'Pilha') -> bool:
        if self.pode_mover_bloco_para(qtd, destino):
            movidas = self.pop(qtd)
            destino.push(movidas)
            if not self.esta_vazia() and not self.topo().virada_para_cima:
                self.topo().virar()
            return True
        return False

    def remover_sequencia_completa(self) -> Optional[List[Carta]]:
        if len(self.cartas) < 13:
            return None
        topo_bloco = self.cartas[-13:]
        if not all(c.virada_para_cima for c in topo_bloco):
            return None
        if topo_bloco[0].valor == 13 and self._sequencia_decrescente_mesmo_naipe(topo_bloco):
            if topo_bloco[-1].valor == 1:
                seq = self.pop(13)
                if not self.esta_vazia() and not self.topo().virada_para_cima:
                    self.topo().virar()
                return seq
        return None


class Baralho:
    def __init__(self):
        # 8 cópias de 1..13 = 104 cartas (Spider 1 naipe)
        self.cartas: List[Carta] = [Carta(v, NAIPE, False) for _ in range(8) for v in range(1, 14)]
        random.shuffle(self.cartas)

    def sacar(self, n: int) -> List[Carta]:
        if n > len(self.cartas):
            raise ValueError("Sem cartas suficientes no baralho.")
        ret = self.cartas[:n]
        self.cartas = self.cartas[n:]
        return ret

    def restante(self) -> int:
        return len(self.cartas)


class Jogo:
    def __init__(self):
        self.tableau: List[Pilha] = [Pilha() for _ in range(10)]
        self.fundacao: List[List[Carta]] = []
        self.estoque = Baralho()

    def iniciar_jogo(self):
        distribuicoes = [6]*4 + [5]*6
        for i, qtd in enumerate(distribuicoes):
            cartas = self.estoque.sacar(qtd)
            self.tableau[i].push(cartas)
        for pilha in self.tableau:
            if not pilha.esta_vazia():
                pilha.topo().virar()

    def distribuir_estoque(self) -> bool:
        if any(p.esta_vazia() for p in self.tableau):
            return False
        if self.estoque.restante() < 10:
            return False
        for pilha in self.tableau:
            carta = self.estoque.sacar(1)[0]
            carta.virar()
            pilha.push([carta])
        return True

    def mover(self, src: int, qtd: int, dst: int) -> bool:
        if not (0 <= src < 10 and 0 <= dst < 10) or src == dst:
            return False
        origem = self.tableau[src]
        destino = self.tableau[dst]
        if qtd <= 0 or qtd > len(origem.cartas):
            return False
        ok = origem.mover_bloco_para(qtd, destino)
        if ok:
            seq = destino.remover_sequencia_completa()
            if seq:
                self.fundacao.append(seq)
        return ok

    def verificar_vitoria(self) -> bool:
        return len(self.fundacao) == 8

    def sem_movimentos_validos(self) -> bool:
        if self.estoque.restante() >= 10 and all(not p.esta_vazia() for p in self.tableau):
            return False
        for i, origem in enumerate(self.tableau):
            start = origem._indice_inicio_bloco_visivel()
            visiveis = len(origem.cartas) - start
            if visiveis <= 0:
                continue
            for qtd in range(1, visiveis+1):
                for j, destino in enumerate(self.tableau):
                    if i == j:
                        continue
                    if origem.pode_mover_bloco_para(qtd, destino):
                        return False
        return True


# =========================
#  Interface Pygame
# =========================

# Tamanho da janela e cartas
LARGURA, ALTURA = 1200, 800
MARGEM_X = 24
TOPO_AREA_Y = 20
CARTA_L, CARTA_A = 90, 120
GAP_X = (LARGURA - 2*MARGEM_X - 10*CARTA_L) // 9  # espaço entre colunas
TOP_TABLEAU_Y = 160
OVERLAP_FACEDOWN = 8
OVERLAP_FACEUP = 28

# Cores
BG = (83, 122, 78)
CARD_FRONT = (240, 240, 240)
CARD_BACK = (41, 43, 102)
CARD_EDGE = (15, 15, 20)
TXT = (25, 25, 25)
TXT_INV = (240, 240, 240)
ACCENT = (220, 180, 30)
DISABLED = (120, 120, 120)

pygame.init()
pygame.display.set_caption("Spider (1 Naipe)")
screen = pygame.display.set_mode((LARGURA, ALTURA))
clock = pygame.time.Clock()
font_big = pygame.font.SysFont(None, 36)
font_med = pygame.font.SysFont(None, 28)
font_small = pygame.font.SysFont(None, 22)

# Botões/áreas
stock_rect = pygame.Rect(MARGEM_X, TOPO_AREA_Y, CARTA_L, CARTA_A)
deal_btn = pygame.Rect(MARGEM_X + CARTA_L + 16, TOPO_AREA_Y + CARTA_A - 34, 120, 28)
restart_btn = pygame.Rect(LARGURA - 180, TOPO_AREA_Y + CARTA_A - 34, 150, 28)

def coluna_x(i: int) -> int:
    return MARGEM_X + i*(CARTA_L + GAP_X)

def pilha_rect(i: int) -> pygame.Rect:
    return pygame.Rect(coluna_x(i), TOP_TABLEAU_Y, CARTA_L, ALTURA - TOP_TABLEAU_Y - 20)

def desenhar_carta(surf, x, y, carta: Carta, elev=False):
    r = pygame.Rect(x, y, CARTA_L, CARTA_A)
    if carta.virada_para_cima:
        pygame.draw.rect(surf, CARD_FRONT, r, border_radius=6)
        pygame.draw.rect(surf, CARD_EDGE, r, 2, border_radius=6)
        txt = font_med.render(str(carta), True, TXT)
        surf.blit(txt, (x + 8, y + 6))
        # valor no canto inferior direito
        txt2 = font_small.render(str(carta), True, TXT)
        surf.blit(txt2, (x + CARTA_L - txt2.get_width() - 8, y + CARTA_A - txt2.get_height() - 6))
    else:
        pygame.draw.rect(surf, CARD_BACK, r, border_radius=6)
        pygame.draw.rect(surf, CARD_EDGE, r, 2, border_radius=6)
        txt = font_small.render("Spider", True, TXT_INV)
        surf.blit(txt, (x + (CARTA_L - txt.get_width())//2, y + (CARTA_A - txt.get_height())//2))
    if elev:
        # sombreado de destaque
        pygame.draw.rect(surf, ACCENT, r, 2, border_radius=6)

def desenhar_ui_topo(jogo: Jogo):
    # Estoque (apenas um slot com contagem)
    pygame.draw.rect(screen, CARD_BACK if jogo.estoque.restante() > 0 else DISABLED, stock_rect, border_radius=6)
    pygame.draw.rect(screen, CARD_EDGE, stock_rect, 2, border_radius=6)
    cnt = font_small.render(str(jogo.estoque.restante()), True, TXT_INV if jogo.estoque.restante() > 0 else (80,80,80))
    screen.blit(cnt, (stock_rect.centerx - cnt.get_width()//2, stock_rect.centery - cnt.get_height()//2))

    # Botão "Estoque"
    can_deal = jogo.estoque.restante() >= 10 and all(not p.esta_vazia() for p in jogo.tableau)
    pygame.draw.rect(screen, (ACCENT if can_deal else DISABLED), deal_btn, border_radius=6)
    label = font_small.render("Distribuir (E)", True, (0,0,0))
    screen.blit(label, (deal_btn.centerx - label.get_width()//2, deal_btn.centery - label.get_height()//2))

    # Fundação / Vitória
    ftxt = font_big.render(f"Fundação: {len(jogo.fundacao)}/8", True, (240,240,240))
    screen.blit(ftxt, (LARGURA//2 - ftxt.get_width()//2, TOPO_AREA_Y + 10))

    # Botão Reiniciar
    pygame.draw.rect(screen, (200, 90, 90), restart_btn, border_radius=6)
    rtxt = font_small.render("Reiniciar (R)", True, (0,0,0))
    screen.blit(rtxt, (restart_btn.centerx - rtxt.get_width()//2, restart_btn.centery - rtxt.get_height()//2))

def desenhar_tableau(jogo: Jogo, drag_info):
    # drag_info: (arrastando:bool, origem_idx:int, cartas:list[Carta], offset:(dx,dy), mouse_pos:(x,y))
    arrastando = drag_info["arrastando"]
    origem_idx = drag_info["origem"]
    drag_cards = drag_info["cartas"]
    mouse_pos = drag_info["mouse"]

    for i, pilha in enumerate(jogo.tableau):
        x = coluna_x(i)
        y = TOP_TABLEAU_Y
        # desenha todas as cartas da pilha; se for a origem e está arrastando, não desenhar as arrastadas
        topo_idx = len(pilha.cartas)
        for idx, carta in enumerate(pilha.cartas):
            is_dragged_piece = arrastando and i == origem_idx and idx >= topo_idx - len(drag_cards)
            if carta.virada_para_cima:
                y_step = OVERLAP_FACEUP
            else:
                y_step = OVERLAP_FACEDOWN
            if not is_dragged_piece:
                desenhar_carta(screen, x, y, carta, elev=False)
            y += y_step

        # se pilha vazia, desenha slot
        if pilha.esta_vazia():
            r = pygame.Rect(x, TOP_TABLEAU_Y, CARTA_L, CARTA_A)
            pygame.draw.rect(screen, (0,0,0), r, 2, border_radius=6)

    # desenhar bloco arrastado por cima de tudo
    if arrastando and drag_cards:
        # alinhar topo do bloco ao mouse com um pequeno offset
        mx, my = mouse_pos
        x0 = mx - CARTA_L//2
        y0 = my - 20
        for k, carta in enumerate(drag_cards):
            desenhar_carta(screen, x0, y0 + k*OVERLAP_FACEUP, carta, elev=True)

def hit_test_pilha(jogo: Jogo, pos: Tuple[int,int]) -> Optional[int]:
    for i in range(10):
        if pilha_rect(i).collidepoint(pos):
            return i
    return None

def ponto_sobre_topo_coluna(i: int, pos: Tuple[int,int]) -> bool:
    # ajuda a decidir o alvo do drop: simplesmente se está dentro da coluna i
    return pilha_rect(i).collidepoint(pos)

def montar_bloco_arrastavel(pilha: Pilha, click_index_from_top: int) -> List[Carta]:
    """
    click_index_from_top: 0 é topo, 1 é a carta logo abaixo do topo, etc.
    Retorna o bloco a partir da carta clicada até o topo, se for uma sequência decrescente e virada.
    Caso contrário, retorna lista vazia.
    """
    n = len(pilha.cartas)
    if click_index_from_top < 0 or click_index_from_top >= n:
        return []
    start_idx = n - 1 - click_index_from_top
    bloco = pilha.cartas[start_idx:]
    if not bloco or not all(c.virada_para_cima for c in bloco):
        return []
    # o bloco inteiro precisa ser uma sequência válida (mesmo naipe e decrescente)
    ok = pilha._sequencia_decrescente_mesmo_naipe(bloco)
    return bloco if ok else []

def coordenada_para_indice_carta(pilha: Pilha, x: int, y: int, col_x: int) -> Optional[int]:
    """
    Retorna o índice a partir do topo (0=topo), considerando overlaps.
    Se clicou acima da primeira carta, None.
    """
    if len(pilha.cartas) == 0:
        return None
    y_cursor = TOP_TABLEAU_Y
    offsets = []
    for c in pilha.cartas:
        offsets.append(y_cursor)
        y_cursor += OVERLAP_FACEUP if c.virada_para_cima else OVERLAP_FACEDOWN
    # região ocupada pela carta do topo (corpo inteiro)
    full_heights = [min(CARTA_A, ALTURA - off) for off in offsets]
    # detectar de baixo pra cima pra favorecer pegar o topo quando há sobreposição
    for idx in reversed(range(len(pilha.cartas))):
        rx = col_x
        ry = offsets[idx]
        r = pygame.Rect(rx, ry, CARTA_L, CARTA_A)
        if r.collidepoint(x, y):
            # converter para "índice a partir do topo"
            from_top = len(pilha.cartas) - 1 - idx
            return from_top
    # clique fora das cartas da pilha
    return None

def main():
    jogo = Jogo()
    jogo.iniciar_jogo()

    drag_info = {
        "arrastando": False,
        "origem": None,
        "cartas": [],
        "mouse": (0, 0)
    }

    msg = ""  # barra de mensagens
    msg_timer = 0

    def set_msg(texto: str, tempo_ms: int = 1800):
        nonlocal msg, msg_timer
        msg = texto
        msg_timer = pygame.time.get_ticks() + tempo_ms

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    jogo = Jogo()
                    jogo.iniciar_jogo()
                    drag_info = {"arrastando": False, "origem": None, "cartas": [], "mouse": (0,0)}
                    set_msg("Novo jogo iniciado.")
                elif event.key == pygame.K_e:
                    if jogo.distribuir_estoque():
                        set_msg("Estoque distribuído.")
                    else:
                        if any(p.esta_vazia() for p in jogo.tableau):
                            set_msg("Não pode distribuir: existe pilha vazia.")
                        elif jogo.estoque.restante() < 10:
                            set_msg("Estoque insuficiente.")
                        else:
                            set_msg("Distribuição não permitida agora.")

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # clique no botão de distribuir
                if deal_btn.collidepoint((mx, my)):
                    if jogo.distribuir_estoque():
                        set_msg("Estoque distribuído.")
                    else:
                        if any(p.esta_vazia() for p in jogo.tableau):
                            set_msg("Não pode distribuir: existe pilha vazia.")
                        elif jogo.estoque.restante() < 10:
                            set_msg("Estoque insuficiente.")
                        else:
                            set_msg("Distribuição não permitida.")
                    continue

                # reiniciar
                if restart_btn.collidepoint((mx, my)):
                    jogo = Jogo()
                    jogo.iniciar_jogo()
                    drag_info = {"arrastando": False, "origem": None, "cartas": [], "mouse": (0,0)}
                    set_msg("Novo jogo iniciado.")
                    continue

                # começar drag numa coluna
                col = hit_test_pilha(jogo, (mx, my))
                if col is not None:
                    pilha = jogo.tableau[col]
                    idx_from_top = coordenada_para_indice_carta(pilha, mx, my, coluna_x(col))
                    if idx_from_top is not None:
                        bloco = montar_bloco_arrastavel(pilha, idx_from_top)
                        if bloco:
                            # marcar arrasto (não removemos ainda; desenhamos por cima e aplicamos no mouseup)
                            drag_info["arrastando"] = True
                            drag_info["origem"] = col
                            drag_info["cartas"] = bloco.copy()
                            drag_info["mouse"] = (mx, my)
                        else:
                            set_msg("Só é possível arrastar uma sequência decrescente virada para cima.")
                    else:
                        # clicar numa pilha vazia não faz nada
                        pass

            elif event.type == pygame.MOUSEMOTION:
                if drag_info["arrastando"]:
                    drag_info["mouse"] = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drag_info["arrastando"]:
                    mx, my = event.pos
                    origem = drag_info["origem"]
                    bloco = drag_info["cartas"]
                    alvo = hit_test_pilha(jogo, (mx, my))
                    if alvo is not None:
                        qtd = len(bloco)
                        # validar contra o estado atual da origem (pode ter mudado), usando o motor
                        if jogo.mover(origem, qtd, alvo):
                            set_msg(f"Movidas {qtd} carta(s): {origem} → {alvo}.")
                        else:
                            set_msg("Movimento inválido.")
                    else:
                        # soltar fora não move
                        pass
                    drag_info = {"arrastando": False, "origem": None, "cartas": [], "mouse": (0,0)}

        # estado final?
        if jogo.verificar_vitoria():
            end_text = "🎉 Vitória! 8 sequências completas."
        elif jogo.sem_movimentos_validos() and jogo.estoque.restante() == 0:
            end_text = "🚫 Travado: sem movimentos e estoque vazio."
        else:
            end_text = ""

        # DRAW
        screen.fill(BG)
        desenhar_ui_topo(jogo)
        desenhar_tableau(jogo, drag_info)

        # mensagem flutuante
        if msg and pygame.time.get_ticks() < msg_timer:
            mtxt = font_small.render(msg, True, (255,255,255))
            screen.blit(mtxt, (MARGEM_X, ALTURA - 30))

        # status final
        if end_text:
            e = font_big.render(end_text, True, (255,255,255))
            pygame.draw.rect(screen, (0, 0, 0), (0, ALTURA - 70, LARGURA, 70))
            screen.blit(e, (MARGEM_X, ALTURA - 56))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
