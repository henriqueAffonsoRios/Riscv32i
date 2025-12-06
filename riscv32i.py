# ---------------------------------------------------------
# Simulador RISC-V
# ---------------------------------------------------------

# -------------------------
# Memória RAM
# -------------------------
class Memory:
    def __init__(self, words=1024):
        self.mem = [0] * words
        self.size_words = words

    def _check_addr(self, addr):
        if addr % 4 != 0:
            raise Exception(f"Unaligned memory access em addr {hex(addr)}")
        idx = addr // 4
        if idx < 0 or idx >= self.size_words:
            raise Exception(f"Memory access out of range: addr={hex(addr)} idx={idx}")
        return idx

    def load_word(self, addr):
        idx = self._check_addr(addr)
        return self.mem[idx]

    def store_word(self, addr, value):
        idx = self._check_addr(addr)
        self.mem[idx] = value & 0xFFFFFFFF

# -------------------------
# Dispositivo de saída (E/S Programada)
# -------------------------
class DisplayOutput:
    MMIO_ADDR = 0xFF00

    def write(self, value):
        print(f"[DISP_OUT] Valor enviado ao dispositivo: {value}")

# -------------------------
# Dispositivo de entrada
# -------------------------
class DisplayInput:
    MMIO_ADDR = 0xFF04 

    def __init__(self):
        self.input_value = 42 

    def read(self):
        print("[DISP_IN] Lendo valor do dispositivo")
        return self.input_value

# ---------------------------------------------------------
# Barramento
# ---------------------------------------------------------
class Bus:
    def __init__(self, memory, disp_out, disp_in):
        self.memory = memory
        self.disp_out = disp_out
        self.disp_in = disp_in

    def load_word(self, addr):
        if addr == self.disp_in.MMIO_ADDR:
            return self.disp_in.read()
        return self.memory.load_word(addr)

    def store_word(self, addr, value):
        if addr == self.disp_out.MMIO_ADDR:
            self.disp_out.write(value)
            return
        self.memory.store_word(addr, value)

# ---------------------------------------------------------
# CPU
# ---------------------------------------------------------
class CPU:
    def __init__(self, bus):
        self.reg = [0] * 32
        self.pc = 0
        self.bus = bus

    def write_reg(self, rd, value):
        if rd != 0:
            self.reg[rd] = value & 0xFFFFFFFF

    def fetch(self, program):
        if self.pc // 4 >= len(program):
            return None
        instr = program[self.pc // 4]
        self.pc += 4
        return instr

    def step(self, program):
        instr = self.fetch(program)
        if instr is None:
            return False

        op = instr.get("op")
        if op is None:
            raise Exception("Instrucao sem campo 'op'")

        try:
            if op == "ADD":
                rd = instr["rd"]; rs1 = instr["rs1"]; rs2 = instr["rs2"]
                self.write_reg(rd, self.reg[rs1] + self.reg[rs2])

            elif op == "SUB":
                rd = instr["rd"]; rs1 = instr["rs1"]; rs2 = instr["rs2"]
                self.write_reg(rd, self.reg[rs1] - self.reg[rs2])

            elif op == "ADDI":
                rd = instr["rd"]; rs1 = instr["rs1"]; imm = instr["imm"]
                self.write_reg(rd, self.reg[rs1] + imm)

            elif op == "AND":
                rd = instr["rd"]; rs1 = instr["rs1"]; rs2 = instr["rs2"]
                self.write_reg(rd, self.reg[rs1] & self.reg[rs2])

            elif op == "OR":
                rd = instr["rd"]; rs1 = instr["rs1"]; rs2 = instr["rs2"]
                self.write_reg(rd, self.reg[rs1] | self.reg[rs2])

            elif op == "XOR":
                rd = instr["rd"]; rs1 = instr["rs1"]; rs2 = instr["rs2"]
                self.write_reg(rd, self.reg[rs1] ^ self.reg[rs2])

            elif op == "LW":
                rd = instr["rd"]; rs1 = instr["rs1"]; imm = instr["imm"]
                addr = (self.reg[rs1] + imm) & 0xFFFFFFFF
                val = self.bus.load_word(addr)
                self.write_reg(rd, val)

            elif op == "SW":
                rs1 = instr["rs1"]; rs2 = instr["rs2"]; imm = instr["imm"]
                addr = (self.reg[rs1] + imm) & 0xFFFFFFFF
                self.bus.store_word(addr, self.reg[rs2])

            else:
                raise Exception(f"Instrução não suportada: {op}")

        except KeyError as e:
            raise Exception(f"Campo faltando na instrução {op}: {e}")

        return True

# ---------------------------------------------------------
# Programa de exemplo (agora incluindo E/S programada)
# ---------------------------------------------------------
programa = [
    {"op": "ADDI", "rd": 1, "rs1": 0, "imm": 10},
    {"op": "ADDI", "rd": 2, "rs1": 0, "imm": 20},

    {"op": "ADD", "rd": 3, "rs1": 1, "rs2": 2},
    {"op": "SUB", "rd": 4, "rs1": 2, "rs2": 1},

    {"op": "AND", "rd": 5, "rs1": 1, "rs2": 2},
    {"op": "OR", "rd": 6, "rs1": 1, "rs2": 2},
    {"op": "XOR", "rd": 7, "rs1": 1, "rs2": 2},

    {"op": "SW", "rs1": 0, "rs2": 3, "imm": 0},
    {"op": "LW", "rd": 8, "rs1": 0, "imm": 0},

    {"op": "SW", "rs1": 0, "rs2": 3, "imm": 0xFF00},
    {"op": "LW", "rd": 9, "rs1": 0, "imm": 0xFF04},
]

# ---------------------------------------------------------
# Execução
# ---------------------------------------------------------
def run():
    memory = Memory()
    disp_out = DisplayOutput()
    disp_in = DisplayInput()
    bus = Bus(memory, disp_out, disp_in)
    cpu = CPU(bus)

    print("Executando programa...\n")

    while cpu.step(programa):
        pass

    print("\nRegistros finais:")
    for i in range(10):
        print(f"x{i} = {cpu.reg[i]}")

    print("\nValor na memória[0]:", memory.mem[0])

# Executa somente se rodado diretamente
if __name__ == "__main__":
    run()
    
# ---------------------------------------------------------
# Explicação das saídas do terminal
# ---------------------------------------------------------
# 1) ADDI x1, x0, 10  → x1 = 10
# 2) ADDI x2, x0, 20  → x2 = 20
#
# 3) ADD x3, x1, x2   → x3 = 10 + 20 = 30
# 4) SUB x4, x2, x1   → x4 = 20 - 10 = 10
#
# 5) AND x5, x1, x2   → 10 & 20 = 0
# 6) OR  x6, x1, x2   → 10 | 20 = 30
# 7) XOR x7, x1, x2   → 10 ^ 20 = 30
#
# 8) SW x3 → mem[0]        (endereço calculado: 0)
#    Resultado: memória[0] = 30
#
# 9) LW x8 ← mem[0]        (carrega 30 de volta)
#
# 10) SW x3 → 0xFF00        (MMIO de saída)
#     Dispara: "[DISP_OUT] Valor enviado ao dispositivo: 30"
#
# 11) LW x9 ← 0xFF04        (MMIO de entrada)
#     Dispara: "[DISP_IN] Lendo valor do dispositivo"
#     x9 recebe o valor fixo do dispositivo (padrão: 0 ou 42, dependendo da config)
#
# Registros impressos (até x5):
# x1 = 10, x2 = 20, x3 = 30, x4 = 10, x5 = 0
#
# Valor final da memória:
# memória[0] = 30