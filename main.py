import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime
import os

# ================ PEGA TUDO DAS VARIÁVEIS ================
TOKEN_BOT = os.getenv("TOKEN_BOT")
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
CANAL_PERMITIDO = int(os.getenv("CANAL_ID", 0))

# CONTROLE DE COOLDOWN
cooldown_user = {}
cooldown_id = {}
# ==================================================

# CONFIGURAÇÃO DO BOT
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# FUNÇÃO QUE CHAMA A API
def chamar_api(id_jogador: str):
    try:
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        dados = {"id_jogador": id_jogador}
        res = requests.post(f"{API_URL}/enviar", json=dados, headers=headers, timeout=30)
        return res.json()
    except Exception as e:
        print(f"Erro: {e}")
        return {"status":"ERRO","mensagem":"Sistema fora do ar, tente novamente mais tarde"}

# QUANDO BOT LIGAR
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ BOT DISCORD LIGADO | {bot.user} | CONECTADO")

# 🎯 COMANDO PRINCIPAL /like
@bot.tree.command(name="like", description="Receba 220 likes no seu perfil Free Fire")
@app_commands.describe(id="Digite apenas os números do seu ID")
async def like(interaction: discord.Interaction, id: str):
    agora = datetime.now()
    user_id = str(interaction.user.id)

    # Verificar se é no canal certo (se configurou)
    if CANAL_PERMITIDO != 0 and interaction.channel.id != CANAL_PERMITIDO:
        return await interaction.response.send_message("❌ Use esse comando apenas no canal correto!", ephemeral=True)

    # Validação do ID
    if not id.isdigit() or len(id) < 8:
        return await interaction.response.send_message("❌ ID inválido! Digite só números, mínimo 8 dígitos.", ephemeral=True)

    # Cooldown usuário
    if user_id in cooldown_user and (agora - cooldown_user[user_id]).total_seconds() < 120:
        tempo = round((120 - (agora - cooldown_user[user_id]).total_seconds())/60, 1)
        return await interaction.response.send_message(f"⏳ Aguarde {tempo} minutos para novo pedido!", ephemeral=True)

    # Cooldown ID
    if id in cooldown_id and (agora - cooldown_id[id]).total_seconds() < 86400:
        return await interaction.response.send_message("⚠️ Esse ID já recebeu likes nas últimas 24h!", ephemeral=True)

    # Avisar que tá processando
    await interaction.response.defer()
    await interaction.followup.send(f"🔄 Processando pedido para ID: `{id}`... Aguarde ~10s")

    # Chamar API
    resposta = chamar_api(id)

    if resposta["status"] == "SUCESSO":
        # Salvar cooldown
        cooldown_user[user_id] = agora
        cooldown_id[id] = agora

        # 🎨 VISUAL IGUAL O QUE VOCÊ QUERIA
        embed = discord.Embed(title="✅ LIKES ENVIADOS COM SUCESSO 🎉", color=0x00FF00, timestamp=datetime.now())
        embed.add_field(name="👤 Usuário", value=f"<@{interaction.user.id}>", inline=False)
        embed.add_field(name="🆔 Free Fire ID", value=f"`{resposta['id']}`", inline=False)
        embed.add_field(name="📋 Informações do Jogador", value=f"Nick: `{resposta['nick']}`\nLevel: {resposta['nivel']}\nRegião: {resposta['regiao']}", inline=False)
        embed.add_field(name="💛 Quantidade", value=f"`{resposta['enviados']}/{resposta['contabilizados']}`", inline=False)
        embed.add_field(name="⏰ Horário", value=resposta['hora'], inline=True)
        embed.add_field(name="🔌 API", value="Automático", inline=True)
        embed.add_field(name="✅ Status", value=f"{resposta['contabilizados']} likes adicionados", inline=False)

        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ Erro: {resposta['mensagem']}")

# 📊 COMANDO STATUS
@bot.tree.command(name="status", description="Verificar status do sistema")
async def status(interaction: discord.Interaction):
    try:
        headers = {"X-API-Key": API_KEY}
        res = requests.get(f"{API_URL}/status", headers=headers, timeout=10).json()
        embed = discord.Embed(title="📊 STATUS DO SISTEMA", color=0x2ECC71)
        embed.add_field(name="🤖 Sistema", value=res["sistema"], inline=False)
        embed.add_field(name="💛 Likes por pedido", value=f"{res['qtd_por_pedido']}", inline=True)
        embed.add_field(name="🚫 Limite diário", value=f"{res['limite_diario']}", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        await interaction.response.send_message("❌ Sistema fora do ar no momento!", ephemeral=True)

bot.run(TOKEN_BOT)
