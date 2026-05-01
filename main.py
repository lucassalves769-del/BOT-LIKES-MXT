import discord
from discord import app_commands
from discord.ext import commands
import requests
import google.generativeai as genai
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# ================ PEGA TUDO PELAS VARIÁVEIS DO RAILWAY =================
TOKEN_BOT = os.getenv("TOKEN_BOT")
GENAI_KEY = os.getenv("GENAI_KEY")
URL_LIKE = os.getenv("URL_LIKE", "https://client.restscape.game.na/us-central1/action/interact/sendLike")
COOKIES = os.getenv("COOKIES", "ssid=ffbr_8927346; game_id=100067; session_id=987654321abcdef; open_id=1971971970")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE5NzE5NzE5NzAsInR5cGUiOjEsImV4cCI6MTc0NjE5Njk5OX0.abcXYZ123456")
# ========================================================================

genai.configure(api_key=GENAI_KEY)
ia = genai.GenerativeModel("gemini-1.5-flash")

cooldown = {}
TEMPO_ESPERA_USUARIO = 120
DELAY_ENTRE_ENVIO = 1.2

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def atualizar_dados():
    try:
        print("🔄 Atualizando dados...")
        sessao = requests.Session()
        sessao.get("https://ff.garena.com", headers={"Cookie": COOKIES})
        global COOKIES
        COOKIES = "; ".join([f"{k}={v}" for k,v in sessao.cookies.get_dict().items()])
        print("✅ Dados atualizados!")
    except:
        print("⚠️ Usando dados padrão")

scheduler = AsyncIOScheduler()
scheduler.add_job(atualizar_dados, "interval", hours=6)

def enviar_um_like(id_alvo: str) -> bool:
    try:
        cabecalhos = {
            "Cookie": COOKIES,
            "Authorization": AUTH_TOKEN,
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36"
        }

        corpo = {
            "uid": id_alvo,
            "type": 1,
            "server_id": "1"
        }

        resposta = requests.post(URL_LIKE, headers=cabecalhos, json=corpo, timeout=15)
        return resposta.status_code == 200

    except:
        return False

async def enviar_varios_likes(id_alvo: str, quantidade: int):
    sucessos = 0
    erros = 0

    for i in range(quantidade):
        if enviar_um_like(id_alvo):
            sucessos +=1
        else:
            erros +=1
        
        await asyncio.sleep(DELAY_ENTRE_ENVIO)

    return sucessos, erros

@tree.command(name="like", description="Envie likes! Use: /like id:xxxx qtd:200")
@app_commands.describe(
    id="Digite o ID do jogador",
    qtd="Quantidade de likes (máximo 200 por vez)"
)
async def like(interaction: discord.Interaction, id: str, qtd: int = 1):
    user_id = interaction.user.id

    if user_id in cooldown:
        tempo = round((cooldown[user_id] - datetime.now()).total_seconds()/60,1)
        await interaction.response.send_message(f"⏳ Espera {tempo} minutos irmão, não pode usar direto!", ephemeral=True)
        return

    if qtd > 200:
        await interaction.response.send_message("❌ Máximo 200 por vez irmão! Se quiser mais, usa de novo depois.", ephemeral=True)
        return

    if not id.isdigit():
        await interaction.followup.send("❌ ID inválido! Exemplo: `/like id:123456789 qtd:200`")
        return

    await interaction.response.defer()
    await interaction.followup.send(f"🚀 Começando envio de {qtd} likes para o ID: `{id}`\n⏳ Aguarde, vai demorar uns {round(qtd*DELAY_ENTRE_ENVIO/60,1)} minutos...")

    sucessos, erros = await enviar_varios_likes(id, qtd)

    msg_final = f"""
✅ FINALIZADO IRMÃO!
🎯 ID: `{id}`
💛 Likes enviados com sucesso: {sucessos}
❌ Falhas: {erros}
    """
    await interaction.followup.send(msg_final)

    cooldown[user_id] = datetime.now() + timedelta(seconds=TEMPO_ESPERA_USUARIO)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    prompt = f"""
    Você é assistente de bot FF, fala igual irmão.
    Comando correto: /like id:seu_id qtd:quantidade (máx 200)
    Exemplo: /like id:123456789 qtd:200
    Usuário disse: {message.content}
    """
    res = ia.generate_content(prompt).text.strip()
    await message.channel.send(res)

@bot.event
async def on_ready():
    await tree.sync()
    scheduler.start()
    print(f"🤖 ONLINE | ENVIO EM MASSA LIBERADO!")

bot.run(TOKEN_BOT)
  
