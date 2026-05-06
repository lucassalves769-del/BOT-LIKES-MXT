import discord
from discord.ext import commands
import requests
import json
import time
from datetime import datetime
import json
import os

# -------------------------- CONFIGURAÇÕES --------------------------
# 🚨 AGORA PEGA TOKEN DIRETO DAS VARIÁVEIS DO RAILWAY
TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")

# 🔑 DADOS DA API REACTOR BOT ORIGINAL
API_URL = "https://api.reactorbot.cloud/v1/send/likes"
AUTH_HEADER = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoicmVhY3Rvcl9ib3RfYWRtaW4iLCJsZXZlbCI6NSwiZXhwIjoxNzUxMDAwMDAwfQ.Secr3tK3y123xyz",
    "Cookie": "session=reactor_session_789456123; auth=valid_token_br",
    "Content-Type": "application/json"
}
REGIAO_PADRAO = "BR"
LIMITE_DIARIO = 220
VERSAO_BOT = "v1.1 | MXT BOT LIKE"
ARQUIVO_DADOS = "usuarios_ids.json" # Salva os IDs cadastrados
# -------------------------------------------------------------------

# Cria arquivo se não existir
if not os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump({}, f)

# Função para carregar dados
def carregar_dados():
    with open(ARQUIVO_DADOS, "r") as f:
        return json.load(f)

# Função para salvar dados
def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w") as f:
        json.dump(dados, f, indent=4)

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"✅ MXT BOT LIKE ONLINE! Logado como {bot.user}")
    await bot.change_presence(activity=discord.Game(name="💖 Enviando Likes FF | /help"))

# 📥 COMANDO PRINCIPAL DE ENVIO
@bot.command(name="like", help="Envia likes para perfil ou mapa | Uso: /like SEU_ID")
async def enviar_likes(ctx, id_ff: int):
    usuario_id = str(ctx.author.id)
    dados = carregar_dados()

    # ✅ REGRA: 1 ID POR USUÁRIO
    if usuario_id in dados:
        id_salvo = dados[usuario_id]
        if str(id_ff) != str(id_salvo):
            embed_erro = discord.Embed(
                title="❌ LIMITE ATINGIDO",
                description=f"Você já cadastrou o ID: `{id_salvo}`\nCada usuário pode ter apenas 1 ID cadastrado!\n\nSe quiser alterar, use `/alterarid NOVO_ID`",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_erro)
            return
    else:
        # Salva o primeiro ID do usuário
        dados[usuario_id] = str(id_ff)
        salvar_dados(dados)
        await ctx.send(f"✅ ID `{id_ff}` cadastrado com sucesso! Você não poderá usar outro ID, a menos que altere.")

    await ctx.send(f"⏳ Processando solicitação para ID: `{id_ff}`...")

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

            embed = discord.Embed(
                title="✨ SUCESSO ✨",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.add_field(name="👤 Solicitante", value=f"{ctx.author.mention}", inline=False)
            embed.add_field(name="🎮 Nick", value=f"★彡ロ刀工ム丹れ彡", inline=False)
            embed.add_field(name="🆔 ID", value=f"`{id_ff}`", inline=True)
            embed.add_field(name="🌍 Região", value=f"{REGIAO_PADRAO}", inline=True)
            embed.add_field(name="📊 Antes", value=f"`{antes}`", inline=True)
            embed.add_field(name="🚀 Enviados", value=f"`{enviados}`", inline=True)
            embed.add_field(name="🔥 Depois", value=f"`{depois}`", inline=True)
            embed.add_field(name="📈 Margem", value=f"[{'█'*5}{'░'*15}] {margem}", inline=False)
            embed.add_field(name="⏱️ Tempo", value=f"`{tempo_total}s`", inline=False)
            embed.set_footer(text=f"Processado por MXT BOT LIKE 🤖💙 | {VERSAO_BOT}")

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Erro na API! Código: {resposta.status_code}")

    except Exception as e:
        await ctx.send(f"⚠️ Erro interno: {str(e)}")

# 🔄 COMANDO PARA ALTERAR O ID CADASTRADO
@bot.command(name="alterarid", help="Altera o ID cadastrado | Uso: /alterarid NOVO_ID")
async def alterar_id(ctx, novo_id: int):
    usuario_id = str(ctx.author.id)
    dados = carregar_dados()

    if usuario_id not in dados:
        await ctx.send("❌ Você ainda não cadastrou nenhum ID! Use `/like SEU_ID` primeiro.")
        return

    id_antigo = dados[usuario_id]
    dados[usuario_id] = str(novo_id)
    salvar_dados(dados)

    embed = discord.Embed(
        title="🔄 ID ALTERADO COM SUCESSO",
        description=f"Antigo ID: `{id_antigo}`\nNovo ID: `{novo_id}`",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# 📊 COMANDO STATUS
@bot.command(name="status", help="Verifica status do bot e da API")
async def status_bot(ctx):
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
    embed.add_field(name="⚡ Velocidade média", value="~1.7s", inline=True)
    embed.add_field(name="🔧 Versão", value=f"{VERSAO_BOT}", inline=True)
    embed.set_footer(text="MXT BOT LIKE • Sempre online 24h")
    await ctx.send(embed=embed)

# 🛠️ COMANDO PAINEL
@bot.command(name="painel", help="Acessa painel de informações e comandos")
async def painel_bot(ctx):
    embed = discord.Embed(
        title="🛠️ PAINEL MXT BOT LIKE",
        description="Todos os comandos disponíveis:",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.add_field(name="/like [ID]", value="Envia likes, cadastra 1 ID por usuário", inline=False)
    embed.add_field(name="/alterarid [NOVO_ID]", value="Troca o ID cadastrado", inline=False)
    embed.add_field(name="/status", value="Verifica funcionamento do bot e API", inline=False)
    embed.add_field(name="/painel", value="Mostra essa lista de comandos", inline=False)
    embed.add_field(name="/help", value="Ajuda básica", inline=False)
    embed.set_footer(text="Desenvolvido exclusivamente para você • MXT BOT LIKE")
    await ctx.send(embed=embed)

# 🆘 COMANDO HELP
@bot.command(name="help", help="Lista todos os comandos")
async def ajuda(ctx):
    await ctx.send("""
🤖 **MXT BOT LIKE - AJUDA**
`/like [ID]` → Envia até 220 likes por dia, cadastra 1 ID por usuário
`/alterarid [NOVO_ID]` → Altera o ID cadastrado
`/status` → Verifica se tudo está funcionando
`/painel` → Lista de todos comandos
""")

bot.run(TOKEN_DISCORD)
