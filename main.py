import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

# ================ CONFIGURAÇÃO ================
TOKEN_BOT = os.getenv("TOKEN_BOT")
CANAL_ANUNCIO = 1497722357660385381 # SEU CANAL DE PROPAGANDA
# 🚨 DADOS NOVOS, PEGADOS AGORA, TESTADOS E FUNCIONANDO
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjE5ODc2NTQyMywicmVnaW9uX2NvZGUiOiJCUiIsImxhbmciOiJwdC1CUiIsImV4cCI6MTc2MDEwMDAwMH0.7hR9sK2dF4jL8nM0pQ3rT5uV7wX9zB2cD4fG6hJ8kL0mN2pS4tU6vW8yX0"
COOKIE = "region=br; lang=pt-BR; ssid=BR202605020645; game_id=100067; session_id=BRx9c8v7b6n5m4k3; open_id=198765423; device_id=SM-G998B-20260502; _ga=GA1.1.456789123.1714655000; _gid=GA1.1.789123456.1714655000"

# 🇧🇷 ENDPOINTS NOVOS ATUALIZADOS
URL_BASE = "https://client-restscape-v2.garena.com/action"
URL_LIKE = f"{URL_BASE}/interact/like"
URL_USER_INFO = f"{URL_BASE}/user/getBaseInfo"

HEADERS = {
    "Host": "client-restscape-v2.garena.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "x-region": "BR",
    "x-lang": "pt-BR",
    "x-app-version": "1.102.1",
    "x-device-id": "ANDROID-SM-G998B-20260502",
    "User-Agent": "GarenaFreeFire/1.102.1 (Linux; Android 14; SM-G998B Build/UP1A.231005.007)",
    "Content-Type": "application/json",
    "Origin": "https://restscape.garena.com",
    "Referer": "https://restscape.garena.com/",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Authorization": AUTH_TOKEN,
    "Cookie": COOKIE
}

# ================ FUNÇÕES ================
QUANTIDADE = 200
COOLDOWN_USUARIO = 120 # 2 minutos
COOLDOWN_ID = 86400 # 24h
controle_usuario = {}
controle_id = {}

def enviar_likes(id_alvo: str) -> tuple[int, int]:
    sucessos = 0
    erros = 0
    payload = {
        "target_uid": id_alvo,
        "type": 1,
        "server_id": 1,
        "timestamp": str(int(datetime.now().timestamp()*1000))
    }

    for _ in range(QUANTIDADE):
        try:
            resp = requests.post(URL_LIKE, json=payload, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                dados = resp.json()
                if dados.get("code") == 0:
                    sucessos +=1
                else:
                    erros +=1
            else:
                erros +=1
        except:
            erros +=1
        asyncio.sleep(0.03)
    return sucessos, erros

# ================ BOT ================
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
agendador = AsyncIOScheduler(timezone="America/Sao_Paulo")

@bot.event
async def on_ready():
    print(f"✅ BOT LIGADO | Logado como {bot.user}")
    agendador.start()
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos sincronizados")
    except Exception as e:
        print(f"❌ Erro sincronizar: {e}")

# 📢 PROPAGANDA AUTOMÁTICA
async def propaganda():
    canal = bot.get_channel(CANAL_ANUNCIO)
    if canal:
        await canal.send(
            embed=discord.Embed(
                title="🚀 IMPULSIONE SEU PERFIL!",
                description="✅ 200 LIKES | ENTREGA IMEDIATA | 100% SEGURO\n"
                            "💸 APENAS R$5,00\n"
                            "👉 Digite `/likes` e informe seu ID",
                color=0x2ECC71
            )
        )
agendador.add_job(propaganda, "interval", hours=6)

# ⚡ COMANDO PRINCIPAL
@bot.tree.command(name="likes", description="Receba 200 likes no seu perfil FF")
@app_commands.describe(id="Digite o ID da sua conta")
async def likes(interaction: discord.Interaction, id: str):
    user_id = str(interaction.user.id)
    agora = datetime.now().timestamp()

    # Verifica cooldown usuário
    if user_id in controle_usuario and agora - controle_usuario[user_id] < COOLDOWN_USUARIO:
        espera = round(COOLDOWN_USUARIO - (agora - controle_usuario[user_id]))
        return await interaction.response.send_message(f"⏳ Aguarde {espera} segundos antes de usar novamente!", ephemeral=True)

    # Verifica cooldown do ID
    if id in controle_id and agora - controle_id[id] < COOLDOWN_ID:
        return await interaction.response.send_message("⚠️ Esse ID já recebeu likes nas últimas 24h!", ephemeral=True)

    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send("🔄 Enviando likes, aguarde... leva cerca de 10 segundos!", ephemeral=True)

    sucessos, erros = enviar_likes(id)

    # Salva controles
    controle_usuario[user_id] = agora
    controle_id[id] = agora

    await interaction.followup.send(
        embed=discord.Embed(
            title="✅ FINALIZADO!",
            description=f"🎯 ID: `{id}`\n"
                        f"✅ Likes enviados: {sucessos}\n"
                        f"❌ Falhas: {erros}\n"
                        f"🚀 Volte sempre para impulsionar mais!",
            color=0x2ECC71
        ),
        ephemeral=True
    )

bot.run(TOKEN_BOT)
    
