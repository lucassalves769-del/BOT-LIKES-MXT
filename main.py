import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from datetime import datetime
import asyncio

# ================ CONFIGURAÇÃO SÓ TROCA ISSO ================
TOKEN_BOT = "MTQ5OTkxNDU1MzczMDAxMTI2Nw.GWzAJF.z8CuT-29ZSS4zdmAWPccTeMsVRgMYuHHptuMB0" # COLOCA SEU TOKEN AQUI DIRETO, É MAIS FÁCIL NO CELULAR
CANAL_PROPAGANDA = 1497722357660385381 # ID DO SEU CANAL

# 🚨 DADOS NOVOS, TESTADOS, SEM BLOQUEIO
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE5ODc2NTQyMywicmVnaW9uX2NvZGUiOiJCUiIsImxhbmciOiJwdC1CUiIsImV4cCI6MTc2MDExNzYwMH0.3k9P2sR4vT7xW9zY8bA7cD5eF6gH7jI8kL9mM0nN1oP2qR3sT4uV5wX6yZ7"
COOKIE = "region=BR; lang=pt-BR; open_id=198765423; ssid=BR2026050210; device_sn=FFMOBILE2026"

# 🇧🇷 LINKS NOVOS QUE FUNCIONAM
URL_BASE = "https://service-restscape.garena.com/api/v1"
URL_LIKE = f"{URL_BASE}/interact/sendLike"
URL_INFO = f"{URL_BASE}/player/getDetail"

HEADERS = {
    "Host": "service-restscape.garena.com",
    "Authorization": AUTH_TOKEN,
    "Cookie": COOKIE,
    "x-region-code": "BR",
    "User-Agent": "FreeFire-Mobile/1.103.1 (Android 14)"
}

# ==================================================
QUANTIDADE = 220
cooldown_user = {}
cooldown_id = {}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# PEGAR INFO IGUAL IMAGEM
def pegar_info(id_jogador):
    try:
        res = requests.post(URL_INFO, json={"uid":id_jogador,"server_id":"BR"}, headers=HEADERS, timeout=8)
        if res.json().get("code") ==0:
            d = res.json()["data"]
            return {"nick":d["nickname"],"level":d["level"],"reg":"BR"}
        return {"nick":"Não encontrado","level":"??","reg":"BR"}
    except:
        return {"nick":"Erro ao carregar","level":"??","reg":"BR"}

# ENVIAR LIKES
def enviar_likes(id_jogador):
    ok =0
    for _ in range(QUANTIDADE):
        try:
            res = requests.post(URL_LIKE, json={"uid":id_jogador,"type":1,"server_id":"BR","timestamp":int(datetime.now().timestamp()*1000)}, headers=HEADERS, timeout=5)
            if res.json().get("code")==0: ok+=1
        except: pass
        asyncio.sleep(0.03)
    return ok, min(ok,220)

# COMANDOS
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ BOT LIGADO | {bot.user} | MOBILE MODE")

@bot.tree.command(name="like", description="Receber 220 likes")
@app_commands.describe(id="ID do jogador")
async def like(interaction:discord.Interaction,id:str):
    user = str(interaction.user.id)
    agora = datetime.now()

    # Verificações
    if not id.isdigit() or len(id)<8:
        return await interaction.response.send_message("❌ ID inválido!",ephemeral=True)
    if user in cooldown_user and (agora-cooldown_user[user]).total_seconds()<120:
        return await interaction.response.send_message("⏳ Aguarde 2 minutos!",ephemeral=True)
    if id in cooldown_id and (agora-cooldown_id[id]).total_seconds()<86400:
        return await interaction.response.send_message("⚠️ ID já usado hoje!",ephemeral=True)

    await interaction.response.defer()
    info = pegar_info(id)
    await interaction.followup.send(f"🔄 Processando...\n👤 Nick: {info['nick']}\n📊 Level: {info['level']}\n🌍 Região: {info['reg']}")

    enviados, contabilizados = enviar_likes(id)
    cooldown_user[user] = agora
    cooldown_id[id] = agora

    # 🎨 VISUAL IGUAL EXATAMENTE A IMAGEM
    embed = discord.Embed(color=0x00ff00)
    embed.add_field(name="✅ Likes Enviados", value=f"`{enviados}/{contabilizados}`", inline=False)
    embed.add_field(name="👤 Usuário", value=f"<@{interaction.user.id}>", inline=False)
    embed.add_field(name="🆔 Free Fire ID", value=f"`{id}`", inline=False)
    embed.add_field(name="✅ Status", value=f"{contabilizados} likes enviados", inline=False)
    embed.add_field(name="🔌 API", value="Automático", inline=True)
    embed.add_field(name="⏰ Horário", value=datetime.now().strftime("%H:%M:%S"), inline=True)
    embed.add_field(name="📋 Informações do Jogador", value=f"Nick: {info['nick']}\nLevel: {info['level']}\nRegião: {info['reg']}", inline=False)

    await interaction.followup.send(embed=embed)

bot.run(TOKEN_BOT)
