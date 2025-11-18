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

    def _indice_inicio_bloco_visivel(self) -> int:
        if self.esta_vazia() or not self.topo().virada_para_cima:
            return len(self.cartas)
        i = len(self.cartas) - 1
        while i >= 0 and self.cartas[i].virada_para_cima:
            i -= 1
        return i + 1

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


# ===== FUNÇÃO DE DICA =====
def encontrar_primeiro_movimento_valido(jogo: Jogo):
    for i, origem in enumerate(jogo.tableau):
        start = origem._indice_inicio_bloco_visivel()
        visiveis = len(origem.cartas) - start
        if visiveis <= 0:
            continue

        for qtd in range(1, visiveis + 1):
            bloco = origem.cartas[-qtd:]
            if not bloco or not all(c.virada_para_cima for c in bloco):
                continue
            if not origem._sequencia_decrescente_mesmo_naipe(bloco):
                continue

            for j, destino in enumerate(jogo.tableau):
                if i == j:
                    continue
                if origem.pode_mover_bloco_para(qtd, destino):
                    return i, qtd, j

    return None


# ============= PYGAME ==============

LARGURA, ALTURA = 1200, 800
MARGEM_X = 24
TOPO_AREA_Y = 20
CARTA_L, CARTA_A = 90, 120

GAP_X = (LARGURA - 2*MARGEM_X - 10*CARTA_L) // 9
TOP_TABLEAU_Y = 160
OVERLAP_FACEDOWN = 8
OVERLAP_FACEUP = 28

# CORES INICIAIS (Modo Claro)
BG = (83, 122, 78)
CARD_FRONT = (240, 240, 240)
CARD_BACK = (41, 43, 102)
CARD_EDGE = (15, 15, 20)
TXT = (25, 25, 25)
TXT_INV = (240, 240, 240)
ACCENT = (220, 180, 30)
DISABLED = (120, 120, 120)

# VARIÁVEL GLOBAL PARA O TEMA
dark_mode = False

# FUNÇÃO PARA TROCAR O TEMA 
def trocar_tema():
    global BG, CARD_FRONT, CARD_BACK, CARD_EDGE, TXT, TXT_INV, ACCENT, DISABLED, dark_mode
    if dark_mode: # Se estiver no escuro, vai para o claro
        BG       = (83, 122, 78)
        CARD_FRONT = (240, 240, 240)
        CARD_BACK  = (41, 43, 102)
        CARD_EDGE  = (15, 15, 20)
        TXT        = (25, 25, 25)
        TXT_INV    = (240, 240, 240)
        ACCENT     = (220, 180, 30)
        DISABLED   = (120, 120, 120)
    else: # Se estiver no claro, vai para o escuro
        BG       = (12, 15, 23)     # fundo escuro elegante
        CARD_FRONT = (62, 68, 92)     # carta clara (muito mais legível!)
        CARD_BACK  = (45, 52, 78)     # verso um pouco mais escuro
        CARD_EDGE  = (200, 200, 220)  # borda clara (destaque perfeito)
        TXT        = (240, 240, 250)  # texto quase branco
        TXT_INV    = (20, 20, 35)     # texto no verso
        ACCENT     = (90, 170, 255)   # azul bonito pro botão
        DISABLED   = (70, 75, 95)
    
    dark_mode = not dark_mode # Alterna o estado


pygame.init()
screen = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Spider (1 Naipe)")
clock = pygame.time.Clock()

font_big = pygame.font.SysFont("DejaVu Sans", 24)
font_med = pygame.font.SysFont("DejaVu Sans", 20)
font_small = pygame.font.SysFont("DejaVu Sans", 18)

# Botões
stock_rect = pygame.Rect(MARGEM_X, TOPO_AREA_Y, CARTA_L, CARTA_A)
deal_btn = pygame.Rect(MARGEM_X + CARTA_L + 16, TOPO_AREA_Y + CARTA_A - 34, 120, 28)
hint_btn = pygame.Rect(MARGEM_X + CARTA_L + 150, TOPO_AREA_Y + CARTA_A - 34, 120, 28)
restart_btn = pygame.Rect(LARGURA - 180, TOPO_AREA_Y + CARTA_A - 34, 150, 28)

# NOVO BOTÃO DE TEMA 
theme_btn = pygame.Rect(LARGURA - 180, TOPO_AREA_Y, 150, 28)


def coluna_x(i: int) -> int:
    return MARGEM_X + i * (CARTA_L + GAP_X)


def pilha_rect(i: int) -> pygame.Rect:
    return pygame.Rect(coluna_x(i), TOP_TABLEAU_Y, CARTA_L, ALTURA - TOP_TABLEAU_Y - 20)


def desenhar_carta(surf, x, y, carta: Carta, elev=False):
    r = pygame.Rect(x, y, CARTA_L, CARTA_A)

    # Fundo
    if carta.virada_para_cima:
        pygame.draw.rect(surf, CARD_FRONT, r, border_radius=8)
        pygame.draw.rect(surf, CARD_EDGE, r, 2, border_radius=8)

        # COR DO NAIPE (apenas ♠ no seu modo atual)
        cor = (0, 0, 0)  # preto padrão

        # Se quiser adicionar ♥ ♦ vermelhos mais tarde, o código já está preparado:
        if carta.naipe in ["♥", "♦"]:
            cor = (200, 30, 30)
        
        # AJUSTE DA COR DO TEXTO PARA LEGIBILIDADE NO MODO ESCURO
        if dark_mode and cor == (0,0,0):
             # Mudar o naipe preto para uma cor mais clara no tema escuro
            cor = (240, 240, 250) 
        elif dark_mode and cor == (200, 30, 30):
             # Mudar o naipe vermelho para uma cor mais clara/saturada no tema escuro (opcional)
             cor = (255, 100, 100)


        valor = VALOR_NOME[carta.valor]
        naipe = carta.naipe

        # TOPO ESQUERDO
        txt_valor = font_small.render(valor, True, cor)
        surf.blit(txt_valor, (x + 8, y + 6))

        txt_naipe = font_med.render(naipe, True, cor)
        surf.blit(txt_naipe, (x + 26, y + 6))

        # RODAPÉ DIREITO (invertido)
        txt_valor2 = font_small.render(valor, True, cor)
        surf.blit(txt_valor2, (x + CARTA_L - txt_valor2.get_width() - 8,
                               y + CARTA_A - txt_valor2.get_height() - 8))

        txt_naipe2 = font_med.render(naipe, True, cor)
        surf.blit(txt_naipe2, (x + CARTA_L - txt_naipe2.get_width() - 26,
                               y + CARTA_A - txt_naipe2.get_height() - 6))

        # NAIPE CENTRAL
        txt_center = pygame.font.SysFont("DejaVu Sans", 36).render(naipe, True, cor)
        surf.blit(txt_center,
                  (x + CARTA_L//2 - txt_center.get_width()//2,
                   y + CARTA_A//2 - txt_center.get_height()//2))

    else:
        # CARTA VIRADA PARA BAIXO
        pygame.draw.rect(surf, CARD_BACK, r, border_radius=8)
        pygame.draw.rect(surf, CARD_EDGE, r, 2, border_radius=8)

        txt = font_small.render("SPIDER", True, TXT_INV)
        surf.blit(txt, (x + (CARTA_L - txt.get_width()) // 2,
                        y + (CARTA_A - txt.get_height()) // 2))

    # HIGHLIGHT (DICA / ARRASTO)
    if elev:
        pygame.draw.rect(surf, (255, 255, 0), r, 4, border_radius=8)


def desenhar_ui_topo(jogo: Jogo):
    # Estoque
    pygame.draw.rect(screen,
                     CARD_BACK if jogo.estoque.restante() > 0 else DISABLED,
                     stock_rect, border_radius=6)
    pygame.draw.rect(screen, CARD_EDGE, stock_rect, 2, border_radius=6)

    cnt = font_small.render(str(jogo.estoque.restante()),
                             True,
                             TXT_INV if jogo.estoque.restante() > 0 else DISABLED)
    screen.blit(cnt, (stock_rect.centerx - cnt.get_width()//2,
                      stock_rect.centery - cnt.get_height()//2))

    # Botão distribuir
    can_deal = jogo.estoque.restante() >= 10 and all(not p.esta_vazia()
                                                     for p in jogo.tableau)
    pygame.draw.rect(screen,
                     ACCENT if can_deal else DISABLED,
                     deal_btn, border_radius=6)
    label = font_small.render("Distribuir (E)", True, TXT_INV if not dark_mode else TXT_INV)
    screen.blit(label, (deal_btn.centerx - label.get_width()//2,
                        deal_btn.centery - label.get_height()//2))

    # Botão de Dica
    hint_color = ACCENT if not dark_mode else (90, 170, 255) # Ajuste a cor da dica para ser visível
    pygame.draw.rect(screen, hint_color, hint_btn, border_radius=6)
    htxt = font_small.render("Dica (H)", True, TXT_INV if not dark_mode else TXT_INV)
    screen.blit(htxt, (hint_btn.centerx - htxt.get_width()//2,
                       hint_btn.centery - htxt.get_height()//2))

    # Fundação
    ftxt = font_big.render(
        f"Fundação: {len(jogo.fundacao)}/8", True, TXT) # Usar TXT para o texto da fundação
    screen.blit(ftxt, (LARGURA//2 - ftxt.get_width()//2, TOPO_AREA_Y + 10))

    # Botão de Tema 
    theme_color = (200, 200, 200) # Cor neutra para o botão
    pygame.draw.rect(screen, theme_color, theme_btn, border_radius=6)
    # O texto deve indicar para qual modo o usuário vai
    theme_text = "Modo Escuro" if not dark_mode else "Modo Claro" 
    ttxt = font_small.render(theme_text, True, (0,0,0))
    screen.blit(ttxt, (theme_btn.centerx - ttxt.get_width()//2,
                        theme_btn.centery - ttxt.get_height()//2))


    # Reiniciar
    pygame.draw.rect(screen, (200, 90, 90), restart_btn, border_radius=6)
    rtxt = font_small.render("Reiniciar (R)", True, (0,0,0))
    screen.blit(rtxt, (restart_btn.centerx - rtxt.get_width()//2,
                       restart_btn.centery - rtxt.get_height()//2))


def desenhar_tableau(jogo: Jogo, drag_info, hint_cards):
    arrastando = drag_info["arrastando"]
    origem_idx = drag_info["origem"]
    drag_cards = drag_info["cartas"]
    mouse_pos = drag_info["mouse"]

    for i, pilha in enumerate(jogo.tableau):
        x = coluna_x(i)
        y = TOP_TABLEAU_Y

        topo_idx = len(pilha.cartas)

        for idx, carta in enumerate(pilha.cartas):
            is_dragged = arrastando and i == origem_idx and idx >= topo_idx - len(drag_cards)

            y_step = OVERLAP_FACEUP if carta.virada_para_cima else OVERLAP_FACEDOWN

            if not is_dragged:
                is_hint = (i, idx) in hint_cards
                desenhar_carta(screen, x, y, carta, elev=is_hint)

            y += y_step

        if pilha.esta_vazia():
            vazio = pygame.Rect(x, TOP_TABLEAU_Y, CARTA_L, CARTA_A)
            # Destaque para slot vazio da dica
            if (i, -1) in hint_cards:
                 pygame.draw.rect(screen, (255, 255, 0), vazio, 4, border_radius=6)
            else:
                 pygame.draw.rect(screen, CARD_EDGE, vazio, 2, border_radius=6)

    if arrastando and drag_cards:
        mx, my = mouse_pos
        x0 = mx - CARTA_L//2
        y0 = my - 20

        for k, carta in enumerate(drag_cards):
            desenhar_carta(screen, x0, y0 + k * OVERLAP_FACEUP, carta, elev=True)


def hit_test_pilha(jogo: Jogo, pos: Tuple[int,int]) -> Optional[int]:
    for i in range(10):
        if pilha_rect(i).collidepoint(pos):
            return i
    return None


def montar_bloco_arrastavel(pilha: Pilha, click_index_from_top: int) -> List[Carta]:
    n = len(pilha.cartas)
    if click_index_from_top < 0 or click_index_from_top >= n:
        return []
    start_idx = n - 1 - click_index_from_top
    bloco = pilha.cartas[start_idx:]
    if not bloco or not all(c.virada_para_cima for c in bloco):
        return []
    return bloco if pilha._sequencia_decrescente_mesmo_naipe(bloco) else []


def coordenada_para_indice_carta(pilha: Pilha, x: int, y: int, col_x: int) -> Optional[int]:
    if len(pilha.cartas) == 0:
        return None

    y_cursor = TOP_TABLEAU_Y
    offsets = []

    for c in pilha.cartas:
        offsets.append(y_cursor)
        y_cursor += OVERLAP_FACEUP if c.virada_para_cima else OVERLAP_FACEDOWN

    for idx in reversed(range(len(pilha.cartas))):
        r = pygame.Rect(col_x, offsets[idx], CARTA_L, CARTA_A)
        if r.collidepoint(x,y):
            return len(pilha.cartas) - 1 - idx

    return None


def main():
    jogo = Jogo()
    jogo.iniciar_jogo()

    drag_info = {"arrastando": False, "origem": None, "cartas": [], "mouse": (0,0)}

    msg = ""
    msg_timer = 0

    hint_cards = set()
    hint_timer = 0  # dica expira sozinha

    def set_msg(texto: str, tempo_ms: int = 1800):
        nonlocal msg, msg_timer
        msg = texto
        msg_timer = pygame.time.get_ticks() + tempo_ms

    running = True
    while running:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            # Teclas
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

                elif event.key == pygame.K_h:
                    mov = encontrar_primeiro_movimento_valido(jogo)
                    hint_cards.clear()

                    if mov:
                        origem_idx, qtd, destino_idx = mov
                        pilha = jogo.tableau[origem_idx]

                        # DESTACAR BLOCO DE ORIGEM
                        start = len(pilha.cartas) - qtd
                        for i in range(start, len(pilha.cartas)):
                            hint_cards.add((origem_idx, i))

                        # DESTACAR DESTINO
                        destino = jogo.tableau[destino_idx]

                        if destino.esta_vazia():
                            # marcar destino vazio usando índice especial (-1)
                            hint_cards.add((destino_idx, -1))
                        else:
                            # marcar carta do topo
                            topo_idx = len(destino.cartas) - 1
                            hint_cards.add((destino_idx, topo_idx))
                        
                        # --- ALTERADO: DEFININDO TIMER PARA TECLA 'H' ---
                        hint_timer = pygame.time.get_ticks() + 3000


            # Clique mouse
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Botão de Tema 
                if theme_btn.collidepoint((mx,my)):
                    trocar_tema()
                    continue

                # Botão distribuir
                if deal_btn.collidepoint((mx,my)):
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

                # Botão reiniciar
                if restart_btn.collidepoint((mx,my)):
                    jogo = Jogo()
                    jogo.iniciar_jogo()
                    drag_info = {"arrastando": False, "origem": None, "cartas": [], "mouse": (0,0)}
                    set_msg("Novo jogo iniciado.")
                    continue
                
                # Botão Dica
                if hint_btn.collidepoint((mx,my)):
                    mov = encontrar_primeiro_movimento_valido(jogo)
                    hint_cards.clear()

                    if mov:
                        origem_idx, qtd, destino_idx = mov

                        # --- DESTACAR ORIGEM ---
                        pilha_origem = jogo.tableau[origem_idx]
                        start = len(pilha_origem.cartas) - qtd

                        for i in range(start, len(pilha_origem.cartas)):
                            hint_cards.add((origem_idx, i))

                        # --- DESTACAR DESTINO ---
                        pilha_dest = jogo.tableau[destino_idx]

                        if pilha_dest.esta_vazia():
                            # marca slot vazio usando índice especial -1
                            hint_cards.add((destino_idx, -1))
                        else:
                            topo_idx = len(pilha_dest.cartas) - 1
                            hint_cards.add((destino_idx, topo_idx))
                        
                        # --- ALTERADO: DEFININDO TIMER PARA CLIQUE DO BOTÃO ---
                        hint_timer = pygame.time.get_ticks() + 3000

                    continue


                # Começar arrasto
                col = hit_test_pilha(jogo, (mx,my))
                if col is not None:
                    pilha = jogo.tableau[col]
                    idx = coordenada_para_indice_carta(pilha, mx, my, coluna_x(col))
                    if idx is not None:
                        bloco = montar_bloco_arrastavel(pilha, idx)
                        if bloco:
                            drag_info = {
                                "arrastando": True,
                                "origem": col,
                                "cartas": bloco.copy(),
                                "mouse": (mx,my)
                            }
                        else:
                            set_msg("Só é possível arrastar sequência válida.")

            elif event.type == pygame.MOUSEMOTION:
                if drag_info["arrastando"]:
                    drag_info["mouse"] = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drag_info["arrastando"]:
                    mx, my = event.pos
                    origem = drag_info["origem"]
                    bloco = drag_info["cartas"]
                    qtd = len(bloco)

                    alvo = hit_test_pilha(jogo, (mx,my))
                    if alvo is not None:
                        if jogo.mover(origem, qtd, alvo):
                            set_msg(f"Movidas {qtd} carta(s).")
                        else:
                            set_msg("Movimento inválido.")

                    drag_info = {"arrastando": False, "origem": None, "cartas": [], "mouse": (0,0)}

        # Vitória / travado
        if jogo.verificar_vitoria():
            end_text = "🎉 Vitória!"
        elif jogo.sem_movimentos_validos() and jogo.estoque.restante() == 0:
            end_text = "🚫 Travado!"
        else:
            end_text = ""

        # Expirar dica
        if hint_timer and pygame.time.get_ticks() > hint_timer:
            hint_cards.clear()
            hint_timer = 0

        # Desenhar
        screen.fill(BG)
        desenhar_ui_topo(jogo)
        desenhar_tableau(jogo, drag_info, hint_cards)

        if msg and pygame.time.get_ticks() < msg_timer:
            mtxt = font_small.render(msg, True, (255,255,255))
            screen.blit(mtxt, (MARGEM_X, ALTURA - 30))

        if end_text:
            e = font_big.render(end_text, True, (255,255,255))
            # Ajuste a cor de fundo da mensagem final para o tema
            bg_end_color = (0,0,0) if not dark_mode else (30, 30, 45) 
            pygame.draw.rect(screen, bg_end_color, (0, ALTURA-70, LARGURA, 70))
            screen.blit(e, (MARGEM_X, ALTURA - 56))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()