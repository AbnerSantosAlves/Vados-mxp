import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from keep_alive import keep_alive

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do bot
TOKEN = os.getenv('DISCORD_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
OWNER_ID = os.getenv('OWNER_ID')
STAFF_CHANNEL_ID = os.getenv('STAFF_CHANNEL_ID')
STAFF_ROLE_ID = os.getenv('STAFF_ROLE_ID')
NARRATOR_ROLE_ID = "1376724323728887969"

# URL da imagem cyberpunk
CYBERPUNK_IMAGE = "https://cdn.discordapp.com/attachments/1253559111497285633/1379311708526350406/a0056e1c1c13074905fb8c31e2b1f8ba.png?ex=683fc7a1&is=683e7621&hm=e9c0914e12a1b4dd6f4115290fa74c49ea0f5a68cd4b30efc6410fa8afc4295a&"

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Intents do bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix=';;', intents=intents, help_command=None)

# Prefix para comandos
PREFIX = ';;'

# Armazenar dados temporários das fichas
temp_staff_data = {}
temp_narrator_data = {}
staff_messages = {}  # Armazenar IDs das mensagens de candidatura
user_processes = {}  # Armazenar IDs de usuários que iniciaram processos

# Status do bot
status_messages = [
    {'name': '🔰 Digite ;;mxp', 'type': discord.ActivityType.playing},
    {'name': '📋 Analisando candidaturas', 'type': discord.ActivityType.watching},
    {'name': '🎯 Madrid Futebol RP MXP', 'type': discord.ActivityType.competing},
    {'name': '⚡ Digite ;;mxp para começar', 'type': discord.ActivityType.playing},
    {'name': '🚀 Sistema de recrutamento', 'type': discord.ActivityType.listening}
]
current_status_index = 0

@tasks.loop(seconds=30)
async def update_status():
    global current_status_index
    if bot.user:
        status = status_messages[current_status_index]
        activity = discord.Activity(name=status['name'], type=status['type'])
        await bot.change_presence(activity=activity)
        current_status_index = (current_status_index + 1) % len(status_messages)

@bot.event
async def on_ready():
    print(f'🤖 Bot {bot.user} está online!')
    print(f'📊 Conectado em {len(bot.guilds)} servidor(es)')
    print(f'👥 Atendendo {len(bot.users)} usuários')
    print(f'🔧 Prefix configurado: {PREFIX}')

    # Sincronizar comandos slash
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} comandos slash sincronizados!')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

    # Iniciar loop de status
    update_status.start()

def can_user_interact(interaction, message_id=None):
    """Verificar se o usuário pode interagir"""
    if message_id:
        message_author = user_processes.get(message_id)
        return not message_author or message_author == interaction.user.id
    return True

def is_owner(user_id):
    """Verificar se é o dono do bot"""
    return str(user_id) == OWNER_ID

def can_edit_category(user):
    """Verificar se pode editar categoria (owner ou cargo específico)"""
    user_id = user.id if hasattr(user, 'id') else user
    
    if is_owner(user_id):
        return True, "owner"
    
    # Verificar se tem o cargo específico autorizado
    authorized_role_id = 1377972129013829672
    if hasattr(user, 'roles'):
        for role in user.roles:
            if role.id == authorized_role_id:
                return True, "authorized_role"
    
    return False, None

class StaffModal1(discord.ui.Modal, title='👮‍♂️ CANDIDATURA STAFF | ETAPA 1/2'):
    def __init__(self):
        super().__init__()

    nome_real = discord.ui.TextInput(
        label='Nome Completo',
        placeholder='Digite seu nome completo aqui...',
        required=True,
        max_length=50
    )

    idade = discord.ui.TextInput(
        label='Idade',
        placeholder='Ex: 18',
        required=True,
        max_length=3
    )

    experiencias = discord.ui.TextInput(
        label='Experiências como Staff',
        placeholder='Descreva suas experiências como staff em outros servidores de RP...',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    motivo = discord.ui.TextInput(
        label='Motivação para ser Staff da MXP',
        placeholder='Por que você quer fazer parte da equipe MXP? O que pode contribuir?',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Verificar se o usuário pode interagir
        if not can_user_interact(interaction):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não pode usar este formulário.',
                ephemeral=True
            )
            return

        # Salvar dados temporariamente
        temp_staff_data[interaction.user.id] = {
            'nome_real': self.nome_real.value,
            'idade': self.idade.value,
            'experiencias': self.experiencias.value,
            'motivo': self.motivo.value,
            'user_id': interaction.user.id,
            'username': interaction.user.name
        }

        embed = discord.Embed(
            title='✅ ETAPA 1 CONCLUÍDA',
            description=f"""```yaml
┌─────────────────────────────────────────┐
│          PRIMEIRA ETAPA COMPLETA        │
│             Dados Salvos ✓              │
└─────────────────────────────────────────┘```
**Perfeito!** Seus dados foram salvos com sucesso.

> **Próximo passo:** Continue para a segunda e última etapa
> **Status:** 🔄 Aguardando confirmação""",
            color=0x00FF00
        )
        embed.add_field(
            name='📊 **PROGRESSO**',
            value='```diff\n+ Etapa 1: ✅ Concluída\n- Etapa 2: ⏳ Pendente```',
            inline=True
        )
        embed.add_field(
            name='⏱️ **TEMPO RESTANTE**',
            value='```fix\nEtapa final - 5 minutos```',
            inline=True
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url=CYBERPUNK_IMAGE)
        embed.timestamp = datetime.now()
        embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

        view = ContinueView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class StaffModal2(discord.ui.Modal, title='👮‍♂️ CANDIDATURA STAFF | ETAPA 2/2'):
    def __init__(self):
        super().__init__()

    preferencia = discord.ui.TextInput(
        label='Área de Preferência',
        placeholder='Parcerias, Invites, Moderação, Eventos, etc...',
        required=True,
        max_length=100
    )

    compromisso = discord.ui.TextInput(
        label='Compromisso com a MXP',
        placeholder='Sim ou Não',
        required=True,
        max_length=10
    )

    hierarquia = discord.ui.TextInput(
        label='Respeito à Hierarquia',
        placeholder='Digite "Sim" para confirmar',
        required=True,
        max_length=10
    )

    disponibilidade = discord.ui.TextInput(
        label='Disponibilidade Semanal',
        placeholder='Quantas horas por semana pode dedicar? Em quais dias/horários?',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Verificar se o usuário pode interagir
        if not can_user_interact(interaction):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não pode usar este formulário.',
                ephemeral=True
            )
            return

        user_data = temp_staff_data.get(interaction.user.id)
        if not user_data:
            await interaction.response.send_message(
                '❌ **ERRO:** Dados da primeira etapa não encontrados. Reinicie o processo com `/mxp`.',
                ephemeral=True
            )
            return

        # Criar embed da ficha
        embed = discord.Embed(
            title='📋 NOVA CANDIDATURA STAFF',
            description=f"""```yaml
┌─────────────────────────────────────────┐
│            MADRID FUTEBOL RP            │
│           CANDIDATURA STAFF             │
└─────────────────────────────────────────┘```""",
            color=0x7289DA
        )
        embed.add_field(
            name='👤 **DADOS PESSOAIS**',
            value=f"```yaml\nNome: {user_data['nome_real']}\nIdade: {user_data['idade']} anos\nUsuário: {user_data['username']}```",
            inline=False
        )
        embed.add_field(
            name='💼 **EXPERIÊNCIAS**',
            value=f"```{user_data['experiencias']}```",
            inline=False
        )
        embed.add_field(
            name='🎯 **MOTIVAÇÃO**',
            value=f"```{user_data['motivo']}```",
            inline=False
        )
        embed.add_field(
            name='🔧 **PREFERÊNCIA**',
            value=f"```fix\n{self.preferencia.value}```",
            inline=True
        )
        embed.add_field(
            name='⏰ **DISPONIBILIDADE**',
            value=f"```{self.disponibilidade.value}```",
            inline=True
        )
        embed.add_field(
            name='📊 **CONFIRMAÇÕES**',
            value=f"```diff\n+ Compromisso: {self.compromisso.value}\n+ Hierarquia: {self.hierarquia.value}```",
            inline=False
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url=CYBERPUNK_IMAGE)
        embed.timestamp = datetime.now()
        embed.set_footer(text=f'ID: {user_data["user_id"]} • MXP VADOS SYSTEM', icon_url=bot.user.display_avatar.url)

        # Botões de aprovação/reprovação
        view = StaffDecisionView(user_data['user_id'])

        try:
            channel = bot.get_channel(int(STAFF_CHANNEL_ID))
            message = await channel.send(embed=embed, view=view)

            # Armazenar ID da mensagem
            staff_messages[user_data['user_id']] = message.id

            success_embed = discord.Embed(
                title='✅ CANDIDATURA ENVIADA',
                description=f"""```yaml
┌─────────────────────────────────────────┐
│         PROCESSO FINALIZADO ✓           │
│        Aguarde a Análise da MXP         │
└─────────────────────────────────────────┘```
**Perfeito!** Sua candidatura foi enviada com sucesso.

> **Status:** 🔄 Em análise pela administração
> **Prazo:** Resposta em até 48 horas
> **Notificação:** Você receberá uma DM com o resultado""",
                color=0x00FF00
            )
            success_embed.add_field(
                name='📋 **PRÓXIMOS PASSOS**',
                value='```fix\n1. Aguarde a análise\n2. Receba notificação por DM\n3. Se aprovado, receba o cargo```',
                inline=False
            )
            success_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            success_embed.set_image(url=CYBERPUNK_IMAGE)
            success_embed.timestamp = datetime.now()
            success_embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

            await interaction.response.send_message(embed=success_embed, ephemeral=True)

            # Limpar dados temporários
            del temp_staff_data[interaction.user.id]

        except Exception as e:
            print(f'Erro ao enviar ficha: {e}')
            await interaction.response.send_message(
                '❌ **ERRO CRÍTICO:** Falha ao enviar candidatura. Contate um administrador.',
                ephemeral=True
            )

class NarratorModal(discord.ui.Modal, title='📖 CADASTRO NARRADOR'):
    def __init__(self):
        super().__init__()

    nome = discord.ui.TextInput(
        label='Nome/Apelido',
        placeholder='Digite seu nome ou apelido...',
        required=True,
        max_length=50
    )

    idade = discord.ui.TextInput(
        label='Idade',
        placeholder='Ex: 18',
        required=True,
        max_length=3
    )

    tempo_livre = discord.ui.TextInput(
        label='Disponibilidade para Narrar',
        placeholder='Quando você está disponível para narrar eventos? Quantas horas por semana?',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=500
    )

    experiencia_narrador = discord.ui.TextInput(
        label='Experiência com Narração',
        placeholder='Já narrou eventos antes? Que tipo de eventos gosta de criar?',
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Verificar se o usuário pode interagir
        if not can_user_interact(interaction):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não pode usar este formulário.',
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title='📖 NOVO CADASTRO NARRADOR',
            description=f"""```yaml
┌─────────────────────────────────────────┐
│            MADRID FUTEBOL RP            │
│           CADASTRO NARRADOR             │
└─────────────────────────────────────────┘```""",
            color=0x9932CC
        )
        embed.add_field(
            name='👤 **DADOS PESSOAIS**',
            value=f"```yaml\nNome: {self.nome.value}\nIdade: {self.idade.value} anos\nUsuário: {interaction.user.name}```",
            inline=False
        )
        embed.add_field(
            name='⏰ **DISPONIBILIDADE**',
            value=f"```{self.tempo_livre.value}```",
            inline=False
        )
        embed.add_field(
            name='🎭 **EXPERIÊNCIA**',
            value=f"```{self.experiencia_narrador.value}```",
            inline=False
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url=CYBERPUNK_IMAGE)
        embed.timestamp = datetime.now()
        embed.set_footer(text=f'ID: {interaction.user.id} • MXP VADOS SYSTEM', icon_url=bot.user.display_avatar.url)

        # Botões de aprovação/reprovação para narrador
        view = NarratorDecisionView(interaction.user.id)

        try:
            channel = bot.get_channel(int(STAFF_CHANNEL_ID))
            message = await channel.send(embed=embed, view=view)

            # Armazenar ID da mensagem
            staff_messages[interaction.user.id] = message.id

            success_embed = discord.Embed(
                title='✅ CADASTRO ENVIADO',
                description=f"""```yaml
┌─────────────────────────────────────────┐
│      CADASTRO ENVIADO COM SUCESSO       │
│        Aguarde Análise da MXP           │
└─────────────────────────────────────────┘```
**Perfeito!** Seu cadastro de narrador foi enviado.

> **Status:** 🔄 Em análise pela administração
> **Prazo:** Resposta em até 48 horas
> **Notificação:** Você receberá uma DM com o resultado""",
                color=0x00FF00
            )
            success_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            success_embed.set_image(url=CYBERPUNK_IMAGE)
            success_embed.timestamp = datetime.now()
            success_embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

            await interaction.response.send_message(embed=success_embed, ephemeral=True)

        except Exception as e:
            print(f'Erro ao enviar cadastro: {e}')
            await interaction.response.send_message(
                '❌ **ERRO CRÍTICO:** Falha ao registrar cadastro. Contate um administrador.',
                ephemeral=True
            )

class MainMenuSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label='CANDIDATURA STAFF',
                description='Candidate-se para ser staff do Madrid Futebol RP MXP',
                value='staff_application',
                emoji='👮‍♂️'
            ),
            discord.SelectOption(
                label='CADASTRO NARRADOR',
                description='Registre-se como narrador de eventos RP',
                value='narrator_application',
                emoji='📖'
            )
        ]
        super().__init__(placeholder='🎯 SELECIONE UMA OPÇÃO...', options=options)

    async def callback(self, interaction: discord.Interaction):
        if not can_user_interact(interaction, interaction.message.id):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não pode interagir com este menu. Use `/mxp` ou `;;mxp` para abrir seu próprio menu.',
                ephemeral=True
            )
            return

        if self.values[0] == 'staff_application':
            modal = StaffModal1()
            await interaction.response.send_modal(modal)
        elif self.values[0] == 'narrator_application':
            modal = NarratorModal()
            await interaction.response.send_modal(modal)

class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        self.add_item(MainMenuSelect())

class ContinueView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label='CONTINUAR PARA ETAPA 2', style=discord.ButtonStyle.primary, emoji='⚡')
    async def continue_step2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_user_interact(interaction):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não pode continuar este processo.',
                ephemeral=True
            )
            return

        modal = StaffModal2()
        await interaction.response.send_modal(modal)

class NarratorDecisionView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label='APROVAR', style=discord.ButtonStyle.success, emoji='✅')
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_decision(interaction, 'approve')

    @discord.ui.button(label='REPROVAR', style=discord.ButtonStyle.danger, emoji='❌')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_decision(interaction, 'reject')

    async def handle_decision(self, interaction: discord.Interaction, action):
        # Verificar se é o owner
        if not is_owner(interaction.user.id):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Apenas o owner do bot pode aprovar/reprovar cadastros.',
                ephemeral=True
            )
            return

        try:
            user = await bot.fetch_user(self.user_id)
            message_id = staff_messages.get(self.user_id)

            if action == 'approve':
                # Adicionar cargo de narrador
                guild = interaction.guild
                member = await guild.fetch_member(self.user_id)
                narrator_role = guild.get_role(int(NARRATOR_ROLE_ID))
                if narrator_role:
                    await member.add_roles(narrator_role)

                # Editar mensagem original
                if message_id:
                    channel = bot.get_channel(int(STAFF_CHANNEL_ID))
                    original_message = await channel.fetch_message(message_id)

                    original_embed = original_message.embeds[0]
                    approved_embed = discord.Embed(
                        title='✅ CADASTRO APROVADO',
                        description=f"{original_embed.description}\n\n```diff\n+ STATUS: APROVADO ✅\n+ Aprovado por: {interaction.user.name}\n+ Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}```",
                        color=0x00FF00
                    )
                    for field in original_embed.fields:
                        approved_embed.add_field(name=field.name, value=field.value, inline=field.inline)

                    if original_embed.thumbnail:
                        approved_embed.set_thumbnail(url=original_embed.thumbnail.url)
                    approved_embed.set_image(url=CYBERPUNK_IMAGE)
                    approved_embed.timestamp = datetime.now()
                    approved_embed.set_footer(text=f'APROVADO • {original_embed.footer.text}', icon_url=original_embed.footer.icon_url)

                    await original_message.edit(embed=approved_embed, view=None)

                # Enviar DM de aprovação
                approve_embed = discord.Embed(
                    title='✅ CADASTRO APROVADO!',
                    description=f"""```yaml
┌─────────────────────────────────────────┐
│       PARABÉNS! VOCÊ FOI APROVADO       │
│        BEM-VINDO À EQUIPE NARRADOR      │
└─────────────────────────────────────────┘```
🎉 **Seu cadastro de narrador foi APROVADO!**

> **Status:** ✅ Narrador oficial da MXP
> **Cargo:** Adicionado automaticamente
> **Próximos passos:** Aguarde instruções dos superiores""",
                    color=0x00FF00
                )
                approve_embed.add_field(
                    name='📖 **MADRID FUTEBOL RP MXP**',
                    value='```diff\n+ Você agora é um narrador oficial\n+ Crie eventos únicos e marcantes\n+ Divirta a comunidade MXP```',
                    inline=False
                )
                approve_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                approve_embed.set_image(url=CYBERPUNK_IMAGE)
                approve_embed.timestamp = datetime.now()
                approve_embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

                try:
                    await user.send(embed=approve_embed)
                except:
                    pass

                await interaction.response.send_message(
                    f'✅ **CADASTRO APROVADO!** {user.name} foi adicionado como narrador.',
                    ephemeral=True
                )

                # Remover da lista de mensagens pendentes
                if self.user_id in staff_messages:
                    del staff_messages[self.user_id]

            elif action == 'reject':
                # Editar mensagem original
                if message_id:
                    channel = bot.get_channel(int(STAFF_CHANNEL_ID))
                    original_message = await channel.fetch_message(message_id)

                    original_embed = original_message.embeds[0]
                    rejected_embed = discord.Embed(
                        title='❌ CADASTRO REPROVADO',
                        description=f"{original_embed.description}\n\n```diff\n- STATUS: REPROVADO ❌\n- Reprovado por: {interaction.user.name}\n- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}```",
                        color=0xFF0000
                    )
                    for field in original_embed.fields:
                        rejected_embed.add_field(name=field.name, value=field.value, inline=field.inline)

                    if original_embed.thumbnail:
                        rejected_embed.set_thumbnail(url=original_embed.thumbnail.url)
                    rejected_embed.set_image(url=CYBERPUNK_IMAGE)
                    rejected_embed.timestamp = datetime.now()
                    rejected_embed.set_footer(text=f'REPROVADO • {original_embed.footer.text}', icon_url=original_embed.footer.icon_url)

                    await original_message.edit(embed=rejected_embed, view=None)

                # Enviar DM de reprovação
                reject_embed = discord.Embed(
                    title='❌ CADASTRO REPROVADO',
                    description=f"""```yaml
┌─────────────────────────────────────────┐
│      CADASTRO NÃO FOI APROVADO         │
│          Não desista! Tente novamente   │
└─────────────────────────────────────────┘```
😔 **Infelizmente seu cadastro não foi aprovado.**

> **Motivo:** A equipe decidiu que você ainda não atende aos critérios
> **Próximos passos:** Continue evoluindo e tente novamente em breve""",
                    color=0xFF0000
                )
                reject_embed.add_field(
                    name='💪 **NÃO DESISTA!**',
                    value='```fix\n• Continue participando da comunidade\n• Mostre mais criatividade\n• Tente novamente no futuro```',
                    inline=False
                )
                reject_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                reject_embed.set_image(url=CYBERPUNK_IMAGE)
                reject_embed.timestamp = datetime.now()
                reject_embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

                try:
                    await user.send(embed=reject_embed)
                except:
                    pass

                await interaction.response.send_message(
                    f'❌ **CADASTRO REPROVADO.** {user.name} foi notificado.',
                    ephemeral=True
                )

                # Remover da lista de mensagens pendentes
                if self.user_id in staff_messages:
                    del staff_messages[self.user_id]

        except Exception as e:
            print(f'Erro ao processar decisão: {e}')
            await interaction.response.send_message(
                '❌ **ERRO:** Falha ao processar decisão. Verifique se o usuário ainda está no servidor.',
                ephemeral=True
            )

class StaffDecisionView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label='APROVAR', style=discord.ButtonStyle.success, emoji='✅')
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_decision(interaction, 'approve')

    @discord.ui.button(label='REPROVAR', style=discord.ButtonStyle.danger, emoji='❌')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_decision(interaction, 'reject')

    async def handle_decision(self, interaction: discord.Interaction, action):
        # Verificar se é o owner
        if not is_owner(interaction.user.id):
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Apenas o owner do bot pode aprovar/reprovar candidaturas.',
                ephemeral=True
            )
            return

        try:
            user = await bot.fetch_user(self.user_id)
            message_id = staff_messages.get(self.user_id)

            if action == 'approve':
                # Adicionar cargos (staff + narrador)
                guild = interaction.guild
                member = await guild.fetch_member(self.user_id)

                # Adicionar cargo de staff
                if STAFF_ROLE_ID:
                    staff_role = guild.get_role(int(STAFF_ROLE_ID))
                    if staff_role:
                        await member.add_roles(staff_role)

                # Adicionar cargo de narrador
                narrator_role = guild.get_role(int(NARRATOR_ROLE_ID))
                if narrator_role:
                    await member.add_roles(narrator_role)

                # Editar mensagem original
                if message_id:
                    channel = bot.get_channel(int(STAFF_CHANNEL_ID))
                    original_message = await channel.fetch_message(message_id)

                    original_embed = original_message.embeds[0]
                    approved_embed = discord.Embed(
                        title='✅ CANDIDATURA APROVADA',
                        description=f"{original_embed.description}\n\n```diff\n+ STATUS: APROVADO ✅\n+ Aprovado por: {interaction.user.name}\n+ Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}```",
                        color=0x00FF00
                    )
                    for field in original_embed.fields:
                        approved_embed.add_field(name=field.name, value=field.value, inline=field.inline)

                    if original_embed.thumbnail:
                        approved_embed.set_thumbnail(url=original_embed.thumbnail.url)
                    approved_embed.set_image(url=CYBERPUNK_IMAGE)
                    approved_embed.timestamp = datetime.now()
                    approved_embed.set_footer(text=f'APROVADO • {original_embed.footer.text}', icon_url=original_embed.footer.icon_url)

                    await original_message.edit(embed=approved_embed, view=None)

                # Enviar DM de aprovação
                approve_embed = discord.Embed(
                    title='✅ CANDIDATURA APROVADA!',
                    description=f"""```yaml
┌─────────────────────────────────────────┐
│        PARABÉNS! VOCÊ FOI APROVADO      │
│         BEM-VINDO À EQUIPE MXP          │
└─────────────────────────────────────────┘```
🎉 **Sua candidatura para staff foi APROVADA!**

> **Status:** ✅ Membro oficial da equipe MXP
> **Cargo:** Adicionado automaticamente
> **Próximos passos:** Aguarde instruções dos superiores""",
                    color=0x00FF00
                )
                approve_embed.add_field(
                    name='🎯 **MADRID FUTEBOL RP MXP**',
                    value='```diff\n+ Você agora faz parte da nossa família\n+ Contribua para o crescimento do servidor\n+ Mantenha sempre o profissionalismo```',
                    inline=False
                )
                approve_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                approve_embed.set_image(url=CYBERPUNK_IMAGE)
                approve_embed.timestamp = datetime.now()
                approve_embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

                try:
                    await user.send(embed=approve_embed)
                except:
                    pass

                await interaction.response.send_message(
                    f'✅ **CANDIDATURA APROVADA!** {user.name} foi adicionado à equipe staff.',
                    ephemeral=True
                )

                # Remover da lista de mensagens pendentes
                if self.user_id in staff_messages:
                    del staff_messages[self.user_id]

            elif action == 'reject':
                # Editar mensagem original
                if message_id:
                    channel = bot.get_channel(int(STAFF_CHANNEL_ID))
                    original_message = await channel.fetch_message(message_id)

                    original_embed = original_message.embeds[0]
                    rejected_embed = discord.Embed(
                        title='❌ CANDIDATURA REPROVADA',
                        description=f"{original_embed.description}\n\n```diff\n- STATUS: REPROVADO ❌\n- Reprovado por: {interaction.user.name}\n- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}```",
                        color=0xFF0000
                    )
                    for field in original_embed.fields:
                        rejected_embed.add_field(name=field.name, value=field.value, inline=field.inline)

                    if original_embed.thumbnail:
                        rejected_embed.set_thumbnail(url=original_embed.thumbnail.url)
                    rejected_embed.set_image(url=CYBERPUNK_IMAGE)
                    rejected_embed.timestamp = datetime.now()
                    rejected_embed.set_footer(text=f'REPROVADO • {original_embed.footer.text}', icon_url=original_embed.footer.icon_url)

                    await original_message.edit(embed=rejected_embed, view=None)

                # Enviar DM de reprovação
                reject_embed = discord.Embed(
                    title='❌ CANDIDATURA REPROVADA',
                    description=f"""```yaml
┌─────────────────────────────────────────┐
│      CANDIDATURA NÃO FOI APROVADA      │
│          Não desista! Tente novamente   │
└─────────────────────────────────────────┘```
😔 **Infelizmente sua candidatura não foi aprovada.**

> **Motivo:** A equipe decidiu que você ainda não atende aos critérios
> **Próximos passos:** Continue evoluindo e tente novamente em breve""",
                    color=0xFF0000
                )
                reject_embed.add_field(
                    name='💪 **NÃO DESISTA!**',
                    value='```fix\n• Continue participando da comunidade\n• Mostre mais engajamento\n• Tente novamente no futuro```',
                    inline=False
                )
                reject_embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
                reject_embed.set_image(url=CYBERPUNK_IMAGE)
                reject_embed.timestamp = datetime.now()
                reject_embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

                try:
                    await user.send(embed=reject_embed)
                except:
                    pass

                await interaction.response.send_message(
                    f'❌ **CANDIDATURA REPROVADA.** {user.name} foi notificado.',
                    ephemeral=True
                )

                # Remover da lista de mensagens pendentes
                if self.user_id in staff_messages:
                    del staff_messages[self.user_id]

        except Exception as e:
            print(f'Erro ao processar decisão: {e}')
            await interaction.response.send_message(
                '❌ **ERRO:** Falha ao processar decisão. Verifique se o usuário ainda está no servidor.',
                ephemeral=True
            )

@bot.tree.command(name='mxp', description='🎯 Menu principal do bot MXP Vados - Sistema de candidaturas')
async def mxp_slash(interaction: discord.Interaction):
    await handle_main_menu(interaction)

async def handle_main_menu(interaction):
    embed = discord.Embed(
        title='🔰 MXP VADOS | SISTEMA DE RECRUTAMENTO',
        description=f"""```yaml
┌─────────────────────────────────────────┐
│           MADRID FUTEBOL RP MXP         │
│              Sistema Oficial            │
└─────────────────────────────────────────┘```
**Bem-vindo ao sistema de candidaturas da MXP!**
> Escolha uma das opções abaixo para prosseguir:""",
        color=0x00FFFF
    )
    embed.add_field(
        name='👮‍♂️ **CANDIDATURA STAFF**',
        value='```fix\n• Faça parte da equipe MXP\n• Processo em 2 etapas\n• Análise rigorosa da administração```',
        inline=True
    )
    embed.add_field(
        name='📖 **CADASTRO NARRADOR**',
        value='```diff\n+ Torne-se narrador oficial\n+ Crie eventos únicos\n+ Divirta a comunidade```',
        inline=True
    )
    embed.add_field(
        name='⚡ **SISTEMA STATUS**',
        value='```css\n[ONLINE] Todos os sistemas operacionais\n[ATIVO] Processamento de candidaturas\n[OK] Conexão estável```',
        inline=False
    )
    embed.set_image(url=CYBERPUNK_IMAGE)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.timestamp = datetime.now()
    embed.set_footer(text='MXP VADOS • Sistema Cyber v2.0', icon_url=bot.user.display_avatar.url)

    view = MainMenuView()

    if hasattr(interaction, 'response'):
        response = await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        message = await interaction.original_response()
    else:
        message = await interaction.send(embed=embed, view=view)

    # Armazenar que este usuário iniciou este processo
    user_processes[message.id] = interaction.author.id if hasattr(interaction, 'author') else interaction.user.id

# Comandos com prefix
@bot.command(name='mxp')
async def mxp_prefix(ctx):
    await handle_main_menu(ctx)

@bot.command(name='menu')
async def menu_prefix(ctx):
    await handle_main_menu(ctx)

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title='🏓 SISTEMA DE LATÊNCIA',
        description=f"""```yaml
┌─────────────────────────────────────────┐
│              TESTE DE PING              │
│            Conexão Verificada           │
└─────────────────────────────────────────┘```""",
        color=0x00FF00
    )
    embed.add_field(
        name='🌐 **LATÊNCIA API**',
        value=f'```fix\n{latency}ms```',
        inline=True
    )
    embed.add_field(
        name='⚡ **STATUS CONEXÃO**',
        value=f'```css\n{"[EXCELENTE]" if latency < 100 else "[BOM]" if latency < 200 else "[LENTO]"}```',
        inline=True
    )
    embed.set_image(url=CYBERPUNK_IMAGE)
    embed.timestamp = datetime.now()
    embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command(name='cyberpunk')
async def cyberpunk_help(ctx):
    embed = discord.Embed(
        title='📚 CENTRAL DE AJUDA',
        description=f"""```yaml
┌─────────────────────────────────────────┐
│            MANUAL DE COMANDOS           │
│              MXP VADOS SYSTEM           │
└─────────────────────────────────────────┘```""",
        color=0x7289DA
    )
    embed.add_field(
        name='🔧 **COMANDOS PREFIX**',
        value=f'```yaml\n{PREFIX}mxp - Abrir menu principal\n{PREFIX}menu - Abrir menu principal\n{PREFIX}ping - Verificar latência\n{PREFIX}cyberpunk - Mostrar ajuda```',
        inline=False
    )
    embed.add_field(
        name='⚡ **COMANDOS SLASH**',
        value='```fix\n/mxp - Menu principal interativo```',
        inline=False
    )
    embed.add_field(
        name='📋 **FUNCIONALIDADES**',
        value='```diff\n+ Sistema de candidatura staff (2 etapas)\n+ Cadastro de narrador\n+ Interface moderna com modais\n+ Notificações automáticas por DM\n+ Sistema de aprovação/reprovação```',
        inline=False
    )
    embed.add_field(
        name='🛡️ **PERMISSÕES**',
        value='```css\n[ADMIN] Apenas o owner pode aprovar candidaturas\n[USER] Qualquer usuário pode se candidatar\n[SYSTEM] Respostas automáticas por DM```',
        inline=False
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_image(url=CYBERPUNK_IMAGE)
    embed.timestamp = datetime.now()
    embed.set_footer(text='MXP VADOS • Sistema Cyber v2.0', icon_url=bot.user.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command(name='ajuda')
async def ajuda(ctx):
    await cyberpunk_help(ctx)

@bot.command(name='help')
async def help_command(ctx):
    await cyberpunk_help(ctx)

@bot.command(name='editcategoria')
async def edit_category(ctx):
    """Comando admin para editar permissões de categoria"""
    can_edit, permission_type = can_edit_category(ctx.author)
    
    if not can_edit:
        embed = discord.Embed(
            title='❌ ACESSO NEGADO',
            description=f"""```yaml
┌─────────────────────────────────────────┐
│           PERMISSÃO INSUFICIENTE        │
│            Acesso Restrito              │
└─────────────────────────────────────────┘```
**Você não tem permissão para usar este comando.**

> **Requerido:** Owner do bot ou cargo autorizado
> **Seu nível:** Usuário comum""",
            color=0xFF0000
        )
        embed.set_image(url=CYBERPUNK_IMAGE)
        embed.timestamp = datetime.now()
        embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed)
        return

    # Mostrar menu inicial com mensagem personalizada
    if permission_type == "owner":
        welcome_msg = f"""```yaml
┌─────────────────────────────────────────┐
│         SISTEMA DE PERMISSÕES           │
│          Edição em Massa                │
│         👑 OWNER YEVGENNYMXP 👑          │
└─────────────────────────────────────────┘```
**🔰 Bem-vindo, YevgennyMXP! Configure permissões para todos os canais de uma categoria**

> **Status:** 👑 Dono Supremo do Bot
> **Funcionalidade:** Editar permissões em massa
> **Alcance:** Todos os canais da categoria selecionada
> **Controle:** Interface GUI completa"""
    else:
        welcome_msg = f"""```yaml
┌─────────────────────────────────────────┐
│         SISTEMA DE PERMISSÕES           │
│          Edição em Massa                │
│        🎯 AUTORIZADO PELO OWNER         │
└─────────────────────────────────────────┘```
**🔰 Acesso autorizado pelo YevgennyMXP! Configure permissões para todos os canais de uma categoria**

> **Status:** ⚡ Membro Autorizado
> **Autorizado por:** 👑 YevgennyMXP (Owner Supremo)
> **Funcionalidade:** Editar permissões em massa
> **Alcance:** Todos os canais da categoria selecionada
> **Controle:** Interface GUI completa"""

    embed = discord.Embed(
        title='🔧 EDITOR DE CATEGORIA',
        description=welcome_msg,
        color=0x00FFFF if permission_type == "owner" else 0xFFD700
    )
    embed.add_field(
        name='📋 **INSTRUÇÕES**',
        value='```fix\n1. Insira o ID da categoria\n2. Insira o ID do cargo\n3. Configure as permissões\n4. Aplique as mudanças```',
        inline=False
    )
    embed.set_image(url=CYBERPUNK_IMAGE)
    embed.timestamp = datetime.now()
    embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

    view = CategoryEditorStartView()
    await ctx.send(embed=embed, view=view)

# Tratar erros
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f'❌ Erro ao processar comando: {error}')

    embed = discord.Embed(
        title='❌ ERRO NO SISTEMA',
        description=f"""```yaml
┌─────────────────────────────────────────┐
│              FALHA DETECTADA            │
│            Sistema Recuperando          │
└─────────────────────────────────────────┘```
**Ocorreu um erro ao processar o comando.**

> **Status:** 🔄 Sistema em recuperação
> **Ação:** Tente novamente em alguns segundos""",
        color=0xFF0000
    )
    embed.set_image(url=CYBERPUNK_IMAGE)
    embed.timestamp = datetime.now()
    embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

    await ctx.send(embed=embed)

class CategoryEditorStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='INICIAR', style=discord.ButtonStyle.primary, emoji='⚡')
    async def start_editing(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CategoryIDModal()
        await interaction.response.send_modal(modal)

class CategoryIDModal(discord.ui.Modal, title='⚙️ CONFIGURAR CATEGORIA'):
    def __init__(self):
        super().__init__()

    category_id = discord.ui.TextInput(
        label='ID da Categoria',
        placeholder='Digite o ID da categoria aqui...',
        required=True,
        max_length=20
    )

    role_id = discord.ui.TextInput(
        label='ID do Cargo',
        placeholder='Digite o ID do cargo aqui...',
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Verificar permissões novamente
        can_edit, permission_type = can_edit_category(interaction.user)
        if not can_edit:
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não tem permissão para usar este comando.',
                ephemeral=True
            )
            return

        try:
            category_id = int(self.category_id.value)
            role_id = int(self.role_id.value)
            
            category = bot.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                await interaction.response.send_message(
                    '❌ **ERRO:** ID da categoria inválido ou categoria não encontrada.',
                    ephemeral=True
                )
                return

            role = category.guild.get_role(role_id)
            if not role:
                await interaction.response.send_message(
                    '❌ **ERRO:** ID do cargo inválido ou cargo não encontrado.',
                    ephemeral=True
                )
                return

            # Mostrar menu de permissões
            embed = discord.Embed(
                title='⚙️ CONFIGURAR PERMISSÕES',
                description=f"""```yaml
┌─────────────────────────────────────────┐
│         EDITAR PERMISSÕES               │
│          Controle Total                 │
└─────────────────────────────────────────┘```
**Configure as permissões para o cargo selecionado.**

> **Cargo:** {role.name}
> **Categoria:** {category.name}
> **Canais:** {len(category.channels)} canais serão afetados""",
                color=0x00FFFF
            )
            embed.add_field(
                name='🔧 **PERMISSÕES DISPONÍVEIS**',
                value='```fix\n• Ver Canal\n• Enviar Mensagens\n• Gerenciar Mensagens\n• Ler Histórico\n• Conectar (Voz)\n• Falar (Voz)```',
                inline=False
            )
            embed.add_field(
                name='📋 **INSTRUÇÕES**',
                value='```css\n[VERDE] = Permitir\n[VERMELHO] = Negar\n[CINZA] = Padrão```',
                inline=False
            )
            embed.set_image(url=CYBERPUNK_IMAGE)
            embed.timestamp = datetime.now()
            embed.set_footer(text='MXP VADOS • Sistema Cyber', icon_url=bot.user.display_avatar.url)

            view = PermissionSelectionView(role, category_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except ValueError:
            await interaction.response.send_message(
                '❌ **ERRO:** IDs devem conter apenas números.',
                ephemeral=True
            )
        except Exception as e:
            print(f'Erro ao processar IDs: {e}')
            await interaction.response.send_message(
                '❌ **ERRO CRÍTICO:** Falha ao processar categoria/cargo. Verifique os IDs.',
                ephemeral=True
            )



class PermissionSelectionView(discord.ui.View):
    def __init__(self, role, category_id):
        super().__init__(timeout=None)
        self.role = role
        self.category_id = category_id
        self.permissions = {}
        self.add_permissions()

    def add_permissions(self):
        self.add_item(PermissionButton('view_channel', 'Ver Canal', self.role, self.category_id, self))
        self.add_item(PermissionButton('send_messages', 'Enviar Mensagens', self.role, self.category_id, self))
        self.add_item(PermissionButton('manage_messages', 'Gerenciar Mensagens', self.role, self.category_id, self))
        self.add_item(PermissionButton('read_message_history', 'Ler Histórico', self.role, self.category_id, self))
        self.add_item(PermissionButton('connect', 'Conectar', self.role, self.category_id, self))
        self.add_item(PermissionButton('speak', 'Falar', self.role, self.category_id, self))

    @discord.ui.button(label='APLICAR', style=discord.ButtonStyle.success, emoji='✅')
    async def apply_permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar permissões
        can_edit, permission_type = can_edit_category(interaction.user)
        if not can_edit:
            await interaction.response.send_message(
                '❌ **ACESSO NEGADO!** Você não tem permissão para usar este comando.',
                ephemeral=True
            )
            return

        category = bot.get_channel(self.category_id)
        if not category:
            await interaction.response.send_message(
                '❌ **ERRO:** Categoria não encontrada.',
                ephemeral=True
            )
            return

        role = category.guild.get_role(self.role.id)
        if not role:
            await interaction.response.send_message(
                '❌ **ERRO:** Cargo não encontrado.',
                ephemeral=True
            )
            return

        # Embed inicial do processo hacker
        hack_embed = discord.Embed(
            title='🔐 INICIANDO PROCESSO DE HACKING',
            description=f"""```ansi
[32m┌─────────────────────────────────────────┐[0m
[32m│          SISTEMA PENETRATION            │[0m
[32m│           EDITANDO PERMISSÕES           │[0m
[32m└─────────────────────────────────────────┘[0m

[33m[INICIANDO][0m Sistema de hack iniciado...
[36m[TARGET][0m Categoria: {category.name}
[36m[TARGET][0m Cargo: {role.name}
[36m[SCANNING][0m {len(category.channels)} canais detectados
[32m[READY][0m Preparando para invasão...```""",
            color=0x00FF00
        )
        hack_embed.set_footer(text='🔐 MXP HACKER SYSTEM • PENETRANDO...', icon_url=bot.user.display_avatar.url)

        await interaction.response.send_message(embed=hack_embed, ephemeral=True)

        # Aguardar um pouco para efeito visual
        await asyncio.sleep(1)

        # Aplicar permissões com logs em tempo real
        logs = []
        successful_channels = 0
        
        for i, channel in enumerate(category.channels):
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                try:
                    permissions = channel.overwrites_for(role)

                    # Aplicar permissões marcadas
                    changes = []
                    for perm, value in self.permissions.items():
                        old_value = getattr(permissions, perm, None)
                        setattr(permissions, perm, value)
                        
                        if value is True:
                            changes.append(f"✅ {perm}")
                        elif value is False:
                            changes.append(f"❌ {perm}")
                        else:
                            changes.append(f"🔄 {perm}")

                    await channel.set_permissions(role, overwrite=permissions)
                    
                    # Log de sucesso
                    channel_type = "🔊" if isinstance(channel, discord.VoiceChannel) else "💬"
                    logs.append(f"[32m[HACKED][0m {channel_type} #{channel.name} - {', '.join(changes[:2])}")
                    successful_channels += 1

                except Exception as e:
                    logs.append(f"[31m[FAILED][0m ❌ #{channel.name} - Erro: {str(e)[:30]}")

                # Atualizar embed a cada 3 canais ou no final
                if (i + 1) % 3 == 0 or i == len(category.channels) - 1:
                    progress = int((i + 1) / len(category.channels) * 100)
                    
                    updated_embed = discord.Embed(
                        title='🔐 HACK EM PROGRESSO',
                        description=f"""```ansi
[32m┌─────────────────────────────────────────┐[0m
[32m│          SISTEMA PENETRATION            │[0m
[32m│        HACKEANDO PERMISSÕES...          │[0m
[32m└─────────────────────────────────────────┘[0m

[33m[PROGRESS][0m {progress}% completo
[36m[TARGET][0m Categoria: {category.name}
[36m[TARGET][0m Cargo: {role.name}

[35m=== LOGS DE INVASÃO ===[0m
{chr(10).join(logs[-10:])}

[32m[STATUS][0m {successful_channels}/{len(category.channels)} canais hackeados```""",
                        color=0x00FF00 if progress == 100 else 0xFFFF00
                    )
                    updated_embed.set_footer(
                        text=f'🔐 MXP HACKER SYSTEM • {progress}% COMPLETO',
                        icon_url=bot.user.display_avatar.url
                    )

                    try:
                        await interaction.edit_original_response(embed=updated_embed)
                        if progress < 100:
                            await asyncio.sleep(0.5)  # Pausa dramática
                    except:
                        pass

        # Embed final de sucesso
        final_embed = discord.Embed(
            title='🔥 NEURAL BREACH COMPLETED',
            description=f"""```ansi
[35m╔═══════════════════════════════════════════╗[0m
[35m║          🚀 CYBERNET INFILTRATION          ║[0m
[35m║         QUANTUM HACK SUCCESSFUL           ║[0m
[35m╚═══════════════════════════════════════════╝[0m

[36m[🔮 NEURAL-LINK][0m Matrix connection established
[32m[⚡ QUANTUM-CORE][0m {category.name} >> BREACHED
[33m[🎯 TARGET-ROLE][0m {role.name} >> COMPROMISED
[32m[💎 DATA-FLOW][0m {successful_channels}/{len(category.channels)} nodes synchronized

[35m╭─── 🌐 CYBER DOMINANCE REPORT ───╮[0m
[32m│ ⚡ Neural pathways reconfigured     │[0m
[32m│ 🔥 Firewall protocols bypassed     │[0m
[32m│ 💾 Memory banks restructured       │[0m
[32m│ 🛡️ Security matrix overwritten     │[0m
[32m│ 🌟 Digital DNA successfully merged │[0m
[35m╰────────────────────────────────────╯[0m

[33m[👑 ARCHITECT][0m YevgennyMXP >> Neo-Tokyo Protocol Active
[36m[🔮 VADOS-AI][0m Permission matrix successfully evolved
[32m[⚡ STATUS][0m Cyberpunk realm fully synchronized```""",
            color=0xFF00FF
        )
        final_embed.set_image(url=CYBERPUNK_IMAGE)
        final_embed.timestamp = datetime.now()
        final_embed.set_footer(text='🔮 VADOS NEURAL NETWORK • QUANTUM BREACH FINALIZED', icon_url=bot.user.display_avatar.url)

        try:
            await interaction.edit_original_response(embed=final_embed)
        except:
            await interaction.followup.send(embed=final_embed, ephemeral=True)

        # Limpar dados temporários
        if interaction.user.id in temp_staff_data:
            del temp_staff_data[interaction.user.id]

class PermissionButton(discord.ui.Button):
    def __init__(self, permission, label, role, category_id, parent_view):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.permission = permission
        self.role = role
        self.category_id = category_id
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Alternar o status da permissão
        current_value = self.parent_view.permissions.get(self.permission, None)

        if current_value is None:
            self.parent_view.permissions[self.permission] = True
            self.style = discord.ButtonStyle.success
            self.label = f"✅ {self.label.replace('❌ ', '').replace('✅ ', '')}"
        elif current_value is True:
            self.parent_view.permissions[self.permission] = False
            self.style = discord.ButtonStyle.danger
            self.label = f"❌ {self.label.replace('❌ ', '').replace('✅ ', '')}"
        else:
            self.parent_view.permissions[self.permission] = None
            self.style = discord.ButtonStyle.secondary
            self.label = self.label.replace('❌ ', '').replace('✅ ', '')

        await interaction.response.edit_message(view=self.parent_view)

# Iniciar servidor keep_alive e bot
if __name__ == "__main__":
    try:
        # Verificar se o token está definido
        if not TOKEN:
            print("❌ ERRO: TOKEN do Discord não encontrado!")
            print("📋 Verifique se a variável DISCORD_TOKEN está definida no arquivo .env")
            exit(1)

        # Iniciar keep_alive
        keep_alive()

        # Iniciar o bot
        print("🚀 Iniciando MXP VADOS Bot...")
        bot.run(TOKEN)

    except discord.LoginFailure:
        print("❌ ERRO: Token do Discord inválido!")
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        print("🔄 Tentando reiniciar em 5 segundos...")
        import time
        time.sleep(5)