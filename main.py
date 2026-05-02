import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# ================ CONFIGURAÇÃO DAS CHAVES ================
TOKEN_BOT = os.getenv("TOKEN_BOT")

# 🇧🇷 DADOS BR ATUALIZADOS
URL_LIKE = os.getenv("URL_LIKE", "https://client.restscape.game.na/us-central1/action/interact/sendLike")
COOKIES = os.getenv("COOKIES", "region=br; lang=pt-BR; ssid=BR7294618; game_id=100067; session_id=BR987654321xyz; open_id=1971971970")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE5NzE5NzE5NzAsInJlZ2lvbl9jb2RlIjoiQlIiLCJsYW5nIjoicHQtQlIiLCJleHAiOjE3NDYxOTY5OTl9.abcBRtoken123456789")
# ==========================================================

# 🚨 REGRAS EXATAS DO FREE FIRE
QUANTIDADE_FIXA = 200       # Sempre envia 200
LIMITE_DIARIO_FF = 220       # Máximo que o FF aceita por dia
COOLDOWN_USUARIO = 120       # 2 minutos entre usos por pessoa
COOLDOWN_ID = 86400          # 24h para mesma ID

# Controle de uso
ids_ja_usados = {}
usuarios_cooldown = {}

DELAY_ENVIO = 1.2 # Tempo entre cada envio pra não dar erro

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ✅ ATUALIZAÇÃO DE DADOS
def atualizar_dados():
    global COOKIES
    try:
        print("🔄 Atualizando dados da API...")
        sessao = requests.Session()
        sessao.get("https://br.garena.com")
        novos_cookies = "; ".join([f"{k}={v}" for k,v in sessao.cookies.get_dict().items()])
        if novos_cookies:
            COOKIES = novos_cookies
        print("✅ Dados BR atualizados com sucesso!")
    except Exception as e:
        print(f"⚠️ Usando dados BR padrão | Erro: {str(e)}")

scheduler = AsyncIOScheduler()
scheduler.add_job(atualizar_dados, "interval", hours=6)

def enviar_um_like(id_alvo: str) -> bool:
    try:
        cabecalhos = {
            "Cookie": COOKIES,
            "Authorization": AUTH_TOKEN,
            "Region": "BR",
            "Accept-Language": "pt-BR",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"
        }

        corpo = {
            "uid": id_alvo,
            "type": 1,
            "server_id": "BR"
        }

        resposta = requests.post(URL_LIKE, headers=cabecalhos, json=corpo, timeout=15)
        return resposta.status_code == 200

    except:
        return False

async def enviar_varios_likes(id_alvo: str):
    sucessos = 0
    erros = 0

    for _ in range(QUANTIDADE_FIXA):
        if enviar_um_like(id_alvo):
            sucessos +=1
        else:
            erros +=1
        await asyncio.sleep(DELAY_ENVIO)

    return sucessos, erros

# COMANDO PRINCIPAL: /like ID
@tree.command(name="like", description="Envia 200 likes | FF BR só aceita 220 por dia")
@app_commands.describe(id="Digite o ID do jogador")
async def like(interaction: discord.Interaction, id: str):
    usuario = interaction.user.id
    agora = datetime.now()

    # Verifica cooldown do usuário
    if usuario in usuarios_cooldown:
        tempo_rest = round((usuarios_cooldown[usuario] - agora).total_seconds()/60,1)
        await interaction.response.send_message(f"⏳ Espera {tempo_rest} min irmão, não pode usar seguido!", ephemeral=True)
        return

    # Verifica se ID já recebeu hoje
    if id in ids_ja_usados:
        tempo_rest = round((ids_ja_usados[id] - agora).total_seconds()/3600,1)
        await interaction.response.send_message(f"⚠️ ID `{id}` já recebeu likes hoje! Volta em {tempo_rest}h | FF BR aceita só {LIMITE_DIARIO_FF}/dia 🚫", ephemeral=True)
        return

    # Verifica se ID é só número
    if not id.isdigit():
        await interaction.response.send_message("❌ ID inválido! Exemplo correto: `/like 123456789`", ephemeral=True)
        return

    await interaction.response.defer()
    await interaction.followup.send(f"""🚀 INICIANDO ENVIO - SERVIDOR BR 🇧🇷
🎯 ID: `{id}`
💛 Quantidade: {QUANTIDADE_FIXA} likes
ℹ️ Regra: FF BR só contabiliza até {LIMITE_DIARIO_FF} por dia!
⏳ Aguarde uns {round(QUANTIDADE_FIXA*DELAY_ENVIO/60,1)} minutos...""")

    sucessos, erros = await enviar_varios_likes(id)

    await interaction.followup.send(f"""✅ FINALIZADO IRMÃO!
🎯 ID: `{id}`
✅ Enviados com sucesso: {sucessos}
❌ Falhas: {erros}
ℹ️ Só vai contar até {LIMITE_DIARIO_FF} likes no jogo, o resto não vale.
🔒 Você só pode usar essa ID novamente amanhã!""")

    # Salva limites
    usuarios_cooldown[usuario] = agora + timedelta(seconds=COOLDOWN_USUARIO)
    ids_ja_usados[id] = agora + timedelta(seconds=COOLDOWN_ID)

# COMANDO DE REGRAS
@tree.command(name="regras", description="Ver as regras e limites do bot BR")
async def regras(interaction: discord.Interaction):
    await interaction.response.send_message(f"""📋 REGRAS DO BOT - SERVIDOR BR 🇧🇷
💛 Envia sempre: {QUANTIDADE_FIXA} likes por uso
🚫 Limite Free Fire BR: {LIMITE_DIARIO_FF} likes por dia/ID
⏱️ Cooldown usuário: 2 minutos entre usos
📅 Mesmo ID só pode usar 1 vez por dia

Comando: `/like ID_DO_JOGADOR`""")

# ✅ RESPOSTAS SIMPLES SEM GROQ/SEM ERRO NENHUM
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content.lower()
    respostas = {
        "oi": "Oi irmão! Tudo certo? Usa /like ID pra pegar seus likes 🇧🇷",
        "ola": "Olá meu parceiro! Quer likes? Só digita /like e o ID!",
        "ajuda": "📋 Comandos disponíveis:\n/like ID → envia 200 likes\n/regras → ver todas regras",
        "comandos": "📋 Comandos disponíveis:\n/like ID → envia 200 likes\n/regras → ver todas regras",
        "como usar": "Basta digitar `/like SEU_ID` exemplo: `/like 123456789` 🚀",
        "limite": "🚫 Limite FF BR: 220 likes por dia, então use só 1 vez por ID por dia!"
    }

    # Procura palavra chave e responde
    for palavra, resposta in respostas.items():
        if palavra in msg:
            await message.channel.send(resposta)
            return

# BOT ONLINE
@bot.event
async def on_ready():
    await tree.sync()
    scheduler.start()
    print(f"\n🤖 BOT ONLINE E FUNCIONANDO - SERVIDOR BR 🇧🇷!")
    print(f"🔗 Conectado como: {bot.user}")
    print(f"📌 Comandos prontos: /like | /regras\n")

bot.run(TOKEN_BOT)
    
