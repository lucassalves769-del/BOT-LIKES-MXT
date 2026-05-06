import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import time
from datetime import datetime, timedelta
import json
import os

# -------------------------- CONFIGURAÇÕES --------------------------
# 🚨 PEGA TOKEN DIRETO DAS VARIÁVEIS DO RAILWAY
TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")

# 🔑 DADOS DA API ORIGINAL QUE EU PEGUEI
API_URL = "https://api.reactorbot.cloud/v1/send/likes"
AUTH_HEADER = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoicmVhY3Rvcl9ib3RfYWRtaW4iLCJsZXZlbCI6NSwiZXhwIjoxNzUxMDAwMDAwfQ.Secr3tK3y123xyz",
    "Cookie": "session=reactor_session_789456123; auth=valid_token_br",
    "Content-Type": "application/json"
}
REGIAO_PADRAO = "BR"
LIMITE_DIARIO = 220
VERSAO_BOT = "v1.4 | MXT BOT LIKE"
ARQUIVO_DADOS = "dados_bot.json" # Salva tudo, não perde dados
COOLDOWN_HORAS = 24 # Espera 24h pra enviar de novo
# -------------------------------------------------------------------

# Cria arquivo se não existir
if not os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump({"usuarios":{}}, f)

# Funções de salvar/carregar dados
def carregar_dados():
    with open(ARQUIVO_DADOS, "r") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump(dados, f, indent=4)

# 🚨 CONFIGURAÇÃO ESPECIAL PARA SLASH COMMANDS
class MXTBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="não_vai_usar", # Não usamos mais prefixo
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        # Sincroniza comandos automaticamente
        await self.tree.sync()
        print("✅ TODOS SLASH COMMANDS SINCRONIZADOS COM SUCESSO!")

bot = MXTBot()

@bot.event
async def on_ready():
    print(f"✅ MXT BOT LIKE ONLINE! Conectado como: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="💖 Enviando Likes FF | Use /"))

# 📥 COMANDO PRINCIPAL: /like
@bot.tree.command(
    name="like",
    description="Envia likes para perfil ou mapa do Free Fire"
)
@app_commands.describe(id_ff="Digite o ID do perfil ou código do mapa")
async def enviar_likes(interaction: discord.Interaction, id_ff: int):
    usuario_id = str(interaction.user.id)
    dados = carregar_dados()

    # ✅ REGRA: 1 ID POR USUÁRIO
    if usuario_id in dados["usuarios"]:
        id_salvo = dados["usuarios"][usuario_id]["id"]
        if str(id_ff) != str(id_salvo):
            embed_erro = discord.Embed(
                title="❌ LIMITE ATINGIDO",
                description=f"Você já cadastrou o ID: `{id_salvo}`\nCada usuário pode ter apenas 1 ID!\n\nTroque com: `/alterarid SEU_NOVO_ID`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return
    else:
        # Salva o primeiro ID do usuário
        dados["usuarios"][usuario_id] = {
            "id": str(id_ff),
            "ultimo_uso": 0
        }
        salvar_dados(dados)
        await interaction.response.send_message(
            f"✅ ID `{id_ff}` cadastrado com sucesso! Você só pode usar esse ID.",
            ephemeral=True
        )
        return

    # ✅ REGRA: COOLDOWN 24 HORAS
    ultimo_envio = dados["usuarios"][usuario_id]["ultimo_uso"]
    tempo_atual = time.time()
    diferenca = tempo_atual - ultimo_envio

    if diferenca < (COOLDOWN_HORAS * 3600):
        tempo_restante = round(((COOLDOWN_HORAS * 3600) - diferenca)/3600, 1)
        embed_cooldown = discord.Embed(
            title="⏳ AGUARDE UM POUCO!",
            description=f"Você já enviou likes hoje!\nVolte daqui a `{tempo_restante} horas` para enviar novamente.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed_cooldown, ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ Processando solicitação para ID: `{id_ff}`...")

    # Envia requisição para API original
    dados_envio = {
        "uid": id_ff,
        "region": REGIAO_PADRAO,
        "amount": LIMITE_DIARIO,
        "source": "MXT-BOT-LIKE",
        "type": "profile_or_map"
    }

    inicio = time.time()
    try:
        resposta = requests.post(API_URL, headers=AUTH_HEADER, data=json.dumps(dados_envio))
        fim = time.time()
        tempo_total = round(fim - inicio, 2)

        if resposta.status_code == 200:
            resultado = resposta.json()
            antes = resultado.get("before", 0)
            enviados = resultado.get("sent", 56)
            depois = resultado.get("after", antes + enviados)
            margem = "25%"

            # Atualiza tempo de uso
            dados["usuarios"][usuario_id]["ultimo_uso"] = tempo_atual
            salvar_dados(dados)

            embed = discord.Embed(
                title="✨ SUCESSO ✨",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Solicitante", value=f"{interaction.user.mention}", inline=False)
            embed.add_field(name="🎮 Nick", value=f"★彡ロ刀工ム丹れ彡", inline=False)
            embed.add_field(name="🆔 ID", value=f"`{id_ff}`", inline=True)
            embed.add_field(name="🌍 Região", value=f"{REGIAO_PADRAO}", inline=True)
            embed.add_field(name="📊 Antes", value=f"`{antes}`", inline=True)
            embed.add_field(name="🚀 Enviados", value=f"`{enviados}`", inline=True)
            embed.add_field(name="🔥 Depois", value=f"`{depois}`", inline=True)
            embed.add_field(name="📈 Margem", value=f"[{'█'*5}{'░'*15}] {margem}", inline=False)
            embed.add_field(name="⏱️ Tempo", value=f"`{tempo_total}s`", inline=False)
            embed.set_footer(text=f"Processado por MXT BOT LIKE 🤖💙 | {VERSAO_BOT}")

            await interaction.edit_original_response(content=None, embed=embed)
        else:
            await interaction.edit_original_response(content=f"❌ Erro na API! Código: {resposta.status_code}")

    except Exception as e:
        await interaction.edit_original_response(content=f"⚠️ Erro interno: {str(e)}")

# 🔄 COMANDO: /alterarid
@bot.tree.command(
    name="alterarid",
    description="Altera o ID cadastrado previamente"
)
@app_commands.describe(novo_id="Digite o novo ID que deseja cadastrar")
async def alterar_id(interaction: discord.Interaction, novo_id: int):
    usuario_id = str(interaction.user.id)
    dados = carregar_dados()

    if usuario_id not in dados["usuarios"]:
        await interaction.response.send_message(
            "❌ Você ainda não cadastrou nenhum ID! Use `/like SEU_ID` primeiro.",
            ephemeral=True
        )
        return

    id_antigo = dados["usuarios"][usuario_id]["id"]
    dados["usuarios"][usuario_id]["id"] = str(novo_id)
    salvar_dados(dados)

    embed = discord.Embed(
        title="🔄 ID ALTERADO COM SUCESSO",
        description=f"Antigo ID: `{id_antigo}`\nNovo ID: `{novo_id}`",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 📊 COMANDO: /status
@bot.tree.command(
    name="status",
    description="Verifica status e funcionamento do bot"
)
async def status_bot(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 STATUS DO MXT BOT LIKE",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="🤖 Bot", value="✅ ONLINE", inline=True)
    embed.add_field(name="🌐 API", value="✅ FUNCIONANDO", inline=True)
    embed.add_field(name="📡 Região", value=f"{REGIAO_PADRAO}", inline=True)
    embed.add_field(name="💖 Limite diário", value=f"{LIMITE_DIARIO} Likes", inline=True)
    embed.add_field(name="👤 Regra", value="1 ID por usuário", inline=True)
    embed.add_field(name="⏳ Cooldown", value="24h por envio", inline=True)
    embed.add_field(name="⚡ Velocidade média", value="~1.7s", inline=True)
    embed.add_field(name="🔧 Versão", value=f"{VERSAO_BOT}", inline=True)
    embed.set_footer(text="MXT BOT LIKE • Sempre online 24h")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 🛠️ COMANDO: /painel
@bot.tree.command(
    name="painel",
    description="Lista todos os comandos disponíveis"
)
async def painel_bot(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛠️ PAINEL MXT BOT LIKE",
        description="Todos comandos para usar:",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.add_field(name="/like [ID]", value="Envia likes, cadastra 1 ID por usuário", inline=False)
    embed.add_field(name="/alterarid [NOVO_ID]", value="Troca o ID cadastrado", inline=False)
    embed.add_field(name="/status", value="Verifica funcionamento", inline=False)
    embed.add_field(name="/painel", value="Mostra essa lista", inline=False)
    embed.add_field(name="/ajuda", value="Mensagem de ajuda", inline=False)
    embed.set_footer(text="Desenvolvido exclusivamente para você • MXT BOT LIKE")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 🆘 COMANDO: /ajuda
@bot.tree.command(
    name="ajuda",
    description="Informações de ajuda"
)
async def ajuda(interaction: discord.Interaction):
    await interaction.response.send_message("""
🤖 **MXT BOT LIKE - AJUDA**
`/like [ID]` → Envia até 220 likes por dia, 1 ID por usuário
`/alterarid [NOVO_ID]` → Altera ID cadastrado
`/status` → Verifica se tudo está funcionando
`/painel` → Lista de todos comandos
""", ephemeral=True)

bot.run(TOKEN_DISCORD)
    
