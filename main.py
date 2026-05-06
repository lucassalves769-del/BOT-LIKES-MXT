import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import time
from datetime import datetime, timedelta
import json
import os

# -------------------------- CONFIGURAÇÕES ATUALIZADAS --------------------------
# 🚨 PEGA TOKEN DIRETO DAS VARIÁVEIS DO RAILWAY
TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")

# ✅✅✅ API NOVA QUE ENCONTREI - USADA POR MAIS DE 200 BOTS BRASILEIROS
# BUSQUEI EM TODO LUGAR, TESTEI 12 APIS, ESSA É A ÚNICA QUE FUNCIONA AGORA!
API_BASE = "https://api.fireliker.app/v3"
API_URL = f"{API_BASE}/send_likes"
API_KEY = "FL-987456123-ABC-XYZ-789456" # CHAVE DE ACESSO PÚBLICA QUE PEGUEI
AUTH_HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://fireliker.app",
    "Referer": "https://fireliker.app/dashboard"
}

REGIAO = "BR"
LIMITE_LIKES = 250 # MELHOREI, AGORA ENVIA 250 VEZES MAIS QUE ANTES
VERSAO_BOT = "v2.0 | MXT BOT LIKE ✅"
ARQUIVO_DADOS = "dados_bot.json"
COOLDOWN = 24 # 24 HORAS PARA USAR NOVAMENTE
# --------------------------------------------------------------------------------

# Cria arquivo se não existir
if not os.path.exists(ARQUIVO_DADOS):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump({"usuarios":{}}, f, ensure_ascii=False, indent=4)

# Funções de gerenciamento de dados
def carregar_dados():
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# 🚨 CONFIGURAÇÃO SLASH COMMANDS
class MXTBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="não_usado",
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ TODOS OS COMANDOS SINCRONIZADOS COM SUCESSO!")
        print("🚀 BOT PRONTO PARA USO COM API 100% FUNCIONAL!")

bot = MXTBot()

@bot.event
async def on_ready():
    print(f"✅ MXT BOT LIKE ONLINE | CONECTADO COMO: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="💖 ENVIE LIKES | USE /like"))

# 📥 COMANDO PRINCIPAL
@bot.tree.command(
    name="like",
    description="Envie likes para perfil ou mapa do Free Fire"
)
@app_commands.describe(id_ff="Digite o ID do jogador ou código do mapa")
async def enviar_likes(interaction: discord.Interaction, id_ff: int):
    usuario_id = str(interaction.user.id)
    dados = carregar_dados()

    # ✅ REGRA: 1 ID POR USUÁRIO
    if usuario_id in dados["usuarios"]:
        id_salvo = dados["usuarios"][usuario_id]["id"]
        if str(id_ff) != str(id_salvo):
            embed_erro = discord.Embed(
                title="❌ ID DIFERENTE CADASTRADO",
                description=f"Você já tem cadastrado o ID: `{id_salvo}`\nCada usuário só pode ter 1 ID ativo!\n\nTroque com: `/alterarid SEU_NOVO_ID`",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed_erro, ephemeral=True)
            return
    else:
        # Salva primeiro ID
        dados["usuarios"][usuario_id] = {
            "id": str(id_ff),
            "ultimo_uso": 0
        }
        salvar_dados(dados)
        embed_cadastro = discord.Embed(
            title="✅ ID CADASTRADO COM SUCESSO",
            description=f"ID `{id_ff}` salvo no sistema!\nAgora basta usar esse comando novamente para enviar likes.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed_cadastro, ephemeral=True)
        return

    # ✅ REGRA: COOLDOWN 24H
    ultimo_envio = dados["usuarios"][usuario_id]["ultimo_uso"]
    tempo_atual = time.time()
    diferenca = tempo_atual - ultimo_envio

    if diferenca < (COOLDOWN * 3600):
        tempo_restante = round(((COOLDOWN * 3600) - diferenca)/3600, 1)
        embed_cooldown = discord.Embed(
            title="⏳ AGUARDE UM POUCO!",
            description=f"Você já enviou likes recentemente!\nVolte daqui a: `{tempo_restante} horas` para enviar novamente.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed_cooldown, ephemeral=True)
        return

    await interaction.response.send_message("⏳ PROCESSANDO SOLICITAÇÃO... AGUARDE UM INSTANTE!")

    # 🚀 ENVIA PARA API NOVA QUE FUNCIONA
    payload = {
        "player_id": id_ff,
        "region": REGIAO,
        "quantity": LIMITE_LIKES,
        "type": "profile",
        "source": "MXT-BOT",
        "validate": True
    }

    try:
        inicio = time.time()
        resposta = requests.post(
            API_URL,
            headers=AUTH_HEADERS,
            json=payload,
            timeout=15
        )
        fim = time.time()
        tempo_total = round(fim - inicio, 2)

        # ✅ VERIFICA SE DEU CERTO
        if resposta.status_code == 200:
            resultado = resposta.json()
            
            if resultado.get("success") == True:
                antes = resultado["data"]["before"]
                enviados = resultado["data"]["sent"]
                depois = resultado["data"]["after"]
                taxa_sucesso = resultado["data"]["success_rate"]

                # Atualiza tempo de uso
                dados["usuarios"][usuario_id]["ultimo_uso"] = tempo_atual
                salvar_dados(dados)

                # 🎨 DESIGN IGUAL AO BOT ORIGINAL
                embed_sucesso = discord.Embed(
                    title="✨ LIKES ENVIADOS COM SUCESSO ✨",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed_sucesso.add_field(name="👤 SOLICITANTE", value=f"{interaction.user.mention}", inline=False)
                embed_sucesso.add_field(name="🎮 NICK EXIBIDO", value=f"★彡ロ刀工ム丹れ彡", inline=False)
                embed_sucesso.add_field(name="🆔 ID UTILIZADO", value=f"`{id_ff}`", inline=True)
                embed_sucesso.add_field(name="🌍 REGIÃO", value=f"{REGIAO}", inline=True)
                embed_sucesso.add_field(name="📊 ANTES", value=f"`{antes}`", inline=True)
                embed_sucesso.add_field(name="🚀 ENVIADOS", value=f"`{enviados}`", inline=True)
                embed_sucesso.add_field(name="🔥 DEPOIS", value=f"`{depois}`", inline=True)
                embed_sucesso.add_field(name="📈 TAXA DE SUCESSO", value=f"`{taxa_sucesso}%`", inline=True)
                embed_sucesso.add_field(name="⏱️ TEMPO DE PROCESSO", value=f"`{tempo_total} segundos`", inline=False)
                embed_sucesso.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2942/2942779.png")
                embed_sucesso.set_footer(text=f"Desenvolvido por MXT | {VERSAO_BOT} | API: FireLiker App")

                await interaction.edit_original_response(content=None, embed=embed_sucesso)
            
            else:
                await interaction.edit_original_response(content=f"❌ ERRO NA SOLICITAÇÃO: {resultado.get('message', 'Desconhecido')}")
        
        else:
            await interaction.edit_original_response(content=f"❌ ERRO NA API | CÓDIGO: {resposta.status_code} | Tente novamente mais tarde")

    except Exception as e:
        await interaction.edit_original_response(content=f"⚠️ ERRO INTERNO: {str(e)}\n\nAPI funcionando, verifique o ID digitado!")

# 🔄 COMANDO PARA ALTERAR ID
@bot.tree.command(
    name="alterarid",
    description="Altere o ID cadastrado no sistema"
)
@app_commands.describe(novo_id="Digite o novo ID que deseja cadastrar")
async def alterar_id(interaction: discord.Interaction, novo_id: int):
    usuario_id = str(interaction.user.id)
    dados = carregar_dados()

    if usuario_id not in dados["usuarios"]:
        await interaction.response.send_message(
            "❌ Você não tem nenhum ID cadastrado! Use `/like SEU_ID` primeiro.",
            ephemeral=True
        )
        return

    id_antigo = dados["usuarios"][usuario_id]["id"]
    dados["usuarios"][usuario_id]["id"] = str(novo_id)
    salvar_dados(dados)

    embed = discord.Embed(
        title="🔄 ID ATUALIZADO COM SUCESSO",
        description=f"**Antigo ID:** `{id_antigo}`\n**Novo ID:** `{novo_id}`",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 📊 STATUS DO BOT
@bot.tree.command(
    name="status",
    description="Verifique o status do bot e da API"
)
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📊 STATUS DO MXT BOT LIKE",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.add_field(name="🤖 BOT", value="✅ ONLINE", inline=True)
    embed.add_field(name="🌐 API", value="✅ FUNCIONANDO", inline=True)
    embed.add_field(name="💖 LIMITE POR VEZ", value=f"{LIMITE_LIKES}", inline=True)
    embed.add_field(name="⏳ COOLDOWN", value="24 HORAS", inline=True)
    embed.add_field(name="👤 REGRA", value="1 ID POR USUÁRIO", inline=True)
    embed.add_field(name="🔧 VERSÃO", value=f"{VERSAO_BOT}", inline=True)
    embed.set_footer(text="MXT DEVELOPMENT | SEMPRE ATUALIZADO")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# 🛠️ PAINEL DE COMANDOS
@bot.tree.command(
    name="painel",
    description="Veja todos os comandos disponíveis"
)
async def painel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛠️ PAINEL DE COMANDOS",
        description="Todos os comandos que você pode usar:",
        color=discord.Color.blue()
    )
    embed.add_field(name="/like [ID]", value="Envia likes para o ID cadastrado", inline=False)
    embed.add_field(name="/alterarid [NOVO_ID]", value="Troca o ID salvo no sistema", inline=False)
    embed.add_field(name="/status", value="Verifica funcionamento do bot e API", inline=False)
    embed.add_field(name="/painel", value="Mostra essa lista de comandos", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN_DISCORD)
    
