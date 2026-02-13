/* Pay2Slay Help – Sherpa Guide with full i18n */
(function () {
  "use strict";

  // ── Translations ──────────────────────────────────────
  var HELP = {
    en: {
      intro: "Your sherpa guide to getting set up and earning Banano for every Fortnite elimination. Follow each section carefully — the account linking part is where most people get stuck.",
      sections: [
        {
          icon: "🏠",
          title: "Step 1 — Join the Discord Server",
          steps: [
            { title: "Open the Invite Link", desc: "Click the <strong>Join Discord Server</strong> button on the login page, or visit our server invite link directly." },
            { title: "Accept the Invite", desc: "If you don't have a Discord account yet, you'll need to create one first. Use a real email you can verify." },
            { title: "Verify Your Email", desc: "Discord may ask you to verify your email before you can interact with the server. Check your inbox (and spam folder)." }
          ],
          tip: "🍌 <strong>Pro tip:</strong> Use the same Discord account everywhere. If you have multiple Discord accounts, make sure you log into Pay2Slay with the one that's in our server."
        },
        {
          icon: "🔗",
          title: "Step 2 — Link Your Epic Games Account (Yunite)",
          steps: [
            { title: "Find the Verification Channel", desc: "In our Discord server, look for a channel called <strong>#verification</strong> or <strong>#link-epic</strong>. Yunite bot posts there." },
            { title: "Click the Link Button", desc: "You'll see a message from <strong>Yunite</strong> with a <strong>Link</strong> button. Click it — a browser window opens." },
            { title: "Sign in to Epic Games", desc: "Log into your <strong>Epic Games account</strong> (the same one you play Fortnite with). Authorize Yunite's access." },
            { title: "Confirm the Link", desc: "Once authorized, Yunite responds in Discord confirming your Epic account is linked. You should see your Epic display name." }
          ],
          tip: "⚠️ <strong>Common pitfall:</strong> Make sure you sign into the correct Epic account — the one you actually play Fortnite on. If you have multiple Epic accounts, only the linked one will track kills."
        },
        {
          icon: "🎮",
          title: "Step 3 — Log In to Pay2Slay",
          steps: [
            { title: "Return to Pay2Slay", desc: "Come back to <strong>pay2slay.cc</strong> and click <strong>Login with Discord</strong>." },
            { title: "Authorize the App", desc: "Discord will ask you to authorize Pay2Slay to read your basic profile. Click <strong>Authorize</strong>." },
            { title: "Automatic Epic Detection", desc: "Pay2Slay automatically finds your Epic ID through Yunite. If linked correctly, your Dashboard will show <strong>Epic Linked: Yes</strong>." }
          ],
          tip: "🔍 <strong>Check your Dashboard:</strong> After logging in, go to the <strong>Dashboard</strong> tab. Look for \"Epic Linked\" — it should say <strong>Yes</strong>. If it says No, you need to re-do Step 2."
        },
        {
          icon: "🍌",
          title: "Step 4 — Set Your Banano Wallet",
          steps: [
            { title: "Get a Wallet", desc: "Download <strong>Kalium</strong> (mobile) or use <strong>vault.banano.cc</strong> (web). Your wallet address starts with <strong>ban_</strong>." },
            { title: "Go to Wallet Tab", desc: "In Pay2Slay, click the <strong>Wallet</strong> tab and paste your <strong>ban_</strong> address." },
            { title: "Save It", desc: "Click <strong>Update</strong>. Your payouts will be sent to this address automatically every settlement cycle." }
          ],
          tip: "💡 <strong>No wallet yet?</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a> is the most popular Banano wallet — it's fast, free, and works on iOS & Android."
        },
        {
          icon: "⚔️",
          title: "Step 5 — Play & Earn",
          steps: [
            { title: "Play Fortnite", desc: "Jump into any public match. Every elimination you get is tracked by the Fortnite API." },
            { title: "Wait for Accrual", desc: "Stats are detected a few minutes after your match ends. Check the <strong>Activity</strong> feed to see your kills appear." },
            { title: "Get Paid", desc: "Every settlement cycle, your accrued Banano is sent to your wallet automatically. No action needed." }
          ],
          tip: "⏱️ <strong>Timing:</strong> Stats usually appear ~5 minutes after the match ends. Settlement happens on a regular cycle shown in the footer countdown."
        }
      ],
      faq: {
        title: "❓ Troubleshooting & FAQ",
        items: [
          { q: "I logged in but my Epic account isn't linked", a: "Go back to our Discord server and complete the Yunite verification (Step 2). Make sure you see the confirmation message from Yunite. Then log out of Pay2Slay and log back in." },
          { q: "I linked the wrong Epic account", a: "In our Discord server, use the Yunite unlink command or button, then redo the link process with the correct Epic account. Log out and back in to Pay2Slay afterward." },
          { q: "My kills aren't showing up", a: "Stats only count from public matches (not Creative, Team Rumble, or private matches). Make sure your Epic account is correct on the Dashboard. Stats appear ~5 minutes after the match ends." },
          { q: "I haven't received my Banano payout", a: "Check that your wallet address is set in the Wallet tab. Payouts happen every settlement cycle (see the countdown in the footer). If your balance is below the minimum payout threshold, it will carry over to the next cycle." },
          { q: "Can I change my wallet address?", a: "Yes — go to the Wallet tab and update it anytime. The new address takes effect on the next settlement." },
          { q: "What's the payout rate per kill?", a: "The per-kill rate depends on the faucet balance and is set by the operators. Check the Dashboard for the current rate." },
          { q: "Discord says 'You need to verify your email'", a: "Go to Discord Settings → My Account → verify your email address. Some servers require verified emails before you can post or interact." }
        ]
      },
      hodl: {
        title: "🚀 $JPMT HODL Boost",
        intro: "Hold <strong>$JPMT</strong> tokens in your Solana wallet to earn boosted Banano payouts on every kill. The more you hold, the higher your multiplier!",
        howTitle: "How It Works",
        howSteps: [
          { title: "Get $JPMT", desc: 'Buy $JPMT on <a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a> using any Solana wallet (Phantom, Solflare, etc.).' },
          { title: "Connect Your Wallet", desc: "On Panel Dashboard, paste your Solana wallet address and click <strong>Verify $JPMT Holdings</strong>." },
          { title: "Get Boosted", desc: "Your tier and multiplier are applied automatically to all future kill payouts. Re-verify anytime to update." }
        ],
        tiersTitle: "Boost Tiers",
        tip: "💎 <strong>Pro tip:</strong> Your boost is based on your balance at verification time. Re-verify after buying more $JPMT to upgrade your tier!",
        links: {
          buy: "Buy $JPMT on Jupiter",
          website: "JPMT Website",
          discord: "JPMT Discord"
        }
      }
    },

    uk: {
      intro: "Ваш провідник-шерпа для налаштування та заробітку Banano за кожне знищення у Fortnite. Уважно дотримуйтесь кожного розділу — саме на прив'язці акаунтів більшість людей стикаються з труднощами.",
      sections: [
        {
          icon: "🏠",
          title: "Крок 1 — Приєднайтесь до Discord сервера",
          steps: [
            { title: "Відкрийте посилання-запрошення", desc: "Натисніть кнопку <strong>Приєднатися до Discord</strong> на сторінці входу або перейдіть за посиланням на наш сервер." },
            { title: "Прийміть запрошення", desc: "Якщо у вас ще немає акаунта Discord, спочатку створіть його. Використовуйте справжню електронну пошту." },
            { title: "Підтвердіть електронну пошту", desc: "Discord може попросити підтвердити вашу пошту. Перевірте вхідні (та папку спам)." }
          ],
          tip: "🍌 <strong>Порада:</strong> Використовуйте один і той самий акаунт Discord скрізь. Переконайтеся, що входите в Pay2Slay з того ж акаунта, що є на нашому сервері."
        },
        {
          icon: "🔗",
          title: "Крок 2 — Прив'яжіть акаунт Epic Games (Yunite)",
          steps: [
            { title: "Знайдіть канал верифікації", desc: "На нашому сервері Discord знайдіть канал <strong>#verification</strong> або <strong>#link-epic</strong>. Бот Yunite публікує там повідомлення." },
            { title: "Натисніть кнопку Link", desc: "Ви побачите повідомлення від <strong>Yunite</strong> з кнопкою <strong>Link</strong>. Натисніть — відкриється вікно браузера." },
            { title: "Увійдіть в Epic Games", desc: "Авторизуйтесь у своєму <strong>акаунті Epic Games</strong> (тому самому, з яким граєте у Fortnite). Дозвольте доступ Yunite." },
            { title: "Підтвердіть прив'язку", desc: "Після авторизації Yunite підтвердить у Discord, що ваш акаунт Epic прив'язано. Ви побачите своє ім'я Epic." }
          ],
          tip: "⚠️ <strong>Часта помилка:</strong> Переконайтеся, що входите в правильний акаунт Epic — той, з яким ви граєте у Fortnite."
        },
        {
          icon: "🎮",
          title: "Крок 3 — Увійдіть у Pay2Slay",
          steps: [
            { title: "Поверніться на Pay2Slay", desc: "Перейдіть на <strong>pay2slay.cc</strong> і натисніть <strong>Login with Discord</strong>." },
            { title: "Авторизуйте додаток", desc: "Discord попросить дозволити Pay2Slay читати ваш профіль. Натисніть <strong>Authorize</strong>." },
            { title: "Автоматичне виявлення Epic", desc: "Pay2Slay автоматично знаходить ваш Epic ID через Yunite. На панелі керування буде <strong>Epic Linked: Yes</strong>." }
          ],
          tip: "🔍 <strong>Перевірте панель:</strong> Після входу перейдіть на вкладку <strong>Dashboard</strong>. Шукайте «Epic Linked» — має бути <strong>Yes</strong>."
        },
        {
          icon: "🍌",
          title: "Крок 4 — Вкажіть гаманець Banano",
          steps: [
            { title: "Отримайте гаманець", desc: "Завантажте <strong>Kalium</strong> (мобільний) або використовуйте <strong>vault.banano.cc</strong>. Адреса починається з <strong>ban_</strong>." },
            { title: "Перейдіть у вкладку Wallet", desc: "У Pay2Slay натисніть вкладку <strong>Wallet</strong> і вставте вашу адресу <strong>ban_</strong>." },
            { title: "Збережіть", desc: "Натисніть <strong>Update</strong>. Виплати надходитимуть на цю адресу автоматично." }
          ],
          tip: "💡 <strong>Немає гаманця?</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a> — найпопулярніший Banano гаманець."
        },
        {
          icon: "⚔️",
          title: "Крок 5 — Грайте та заробляйте",
          steps: [
            { title: "Грайте у Fortnite", desc: "Заходьте в будь-який публічний матч. Кожне ваше знищення відстежується API Fortnite." },
            { title: "Чекайте нарахування", desc: "Статистика з'являється через кілька хвилин після закінчення матчу. Перевіряйте стрічку <strong>Activity</strong>." },
            { title: "Отримуйте оплату", desc: "Кожен цикл розрахунку ваші Banano надсилаються на гаманець автоматично." }
          ],
          tip: "⏱️ <strong>Час:</strong> Статистика зазвичай з'являється ~5 хвилин після закінчення матчу."
        }
      ],
      faq: {
        title: "❓ Вирішення проблем та FAQ",
        items: [
          { q: "Я увійшов, але мій Epic не прив'язаний", a: "Поверніться на Discord сервер і завершіть верифікацію Yunite (Крок 2). Потім вийдіть з Pay2Slay і увійдіть знову." },
          { q: "Я прив'язав неправильний акаунт Epic", a: "На Discord сервері використайте команду відв'язки Yunite, потім повторіть прив'язку з правильним акаунтом." },
          { q: "Мої кіли не відображаються", a: "Статистика рахується лише з публічних матчів. Перевірте акаунт Epic на Dashboard." },
          { q: "Я не отримав виплату Banano", a: "Перевірте адресу гаманця у вкладці Wallet. Виплати відбуваються кожен цикл розрахунку." },
          { q: "Чи можу я змінити адресу гаманця?", a: "Так — перейдіть у вкладку Wallet і оновіть адресу в будь-який час." },
          { q: "Який коефіцієнт виплати за кіл?", a: "Коефіцієнт залежить від балансу фонду і встановлюється операторами." },
          { q: "Discord каже 'Потрібно підтвердити email'", a: "Налаштування Discord → Мій акаунт → підтвердіть вашу email адресу." }
        ]
      },
      hodl: {
        title: "🚀 Буст $JPMT HODL",
        intro: "Тримайте токени <strong>$JPMT</strong> у вашому Solana гаманці, щоб отримувати підвищені виплати Banano за кожен кіл. Чим більше тримаєте, тим вищий множник!",
        howTitle: "Як це працює",
        howSteps: [
          { title: "Отримайте $JPMT", desc: 'Купіть $JPMT на <a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a> використовуючи будь-який Solana гаманець.' },
          { title: "Підключіть гаманець", desc: "На Dashboard вставте вашу адресу Solana гаманця і натисніть <strong>Verify $JPMT Holdings</strong>." },
          { title: "Отримайте буст", desc: "Ваш рівень і множник застосовуються автоматично. Перевіряйте знову після покупки нових $JPMT." }
        ],
        tiersTitle: "Рівні бусту",
        tip: "💎 <strong>Порада:</strong> Буст базується на балансі під час верифікації. Перевірте знову після покупки більше $JPMT!",
        links: { buy: "Купити $JPMT на Jupiter", website: "Сайт JPMT", discord: "Discord JPMT" }
      }
    },

    es: {
      intro: "Tu guía sherpa para configurar todo y ganar Banano por cada eliminación en Fortnite. Sigue cada sección con cuidado — la vinculación de cuentas es donde la mayoría se atasca.",
      sections: [
        {
          icon: "🏠",
          title: "Paso 1 — Únete al servidor de Discord",
          steps: [
            { title: "Abre el enlace de invitación", desc: "Haz clic en el botón <strong>Unirse a Discord</strong> en la página de inicio de sesión." },
            { title: "Acepta la invitación", desc: "Si no tienes una cuenta de Discord, crea una primero. Usa un correo real que puedas verificar." },
            { title: "Verifica tu correo", desc: "Discord puede pedirte que verifiques tu correo. Revisa tu bandeja de entrada (y la carpeta de spam)." }
          ],
          tip: "🍌 <strong>Consejo:</strong> Usa la misma cuenta de Discord en todas partes. Asegúrate de iniciar sesión en Pay2Slay con la misma cuenta que está en nuestro servidor."
        },
        {
          icon: "🔗",
          title: "Paso 2 — Vincula tu cuenta de Epic Games (Yunite)",
          steps: [
            { title: "Encuentra el canal de verificación", desc: "En nuestro servidor de Discord, busca el canal <strong>#verification</strong> o <strong>#link-epic</strong>." },
            { title: "Haz clic en el botón Link", desc: "Verás un mensaje de <strong>Yunite</strong> con un botón <strong>Link</strong>. Haz clic — se abrirá una ventana del navegador." },
            { title: "Inicia sesión en Epic Games", desc: "Entra en tu <strong>cuenta de Epic Games</strong> (la misma con la que juegas Fortnite). Autoriza el acceso de Yunite." },
            { title: "Confirma la vinculación", desc: "Yunite confirmará en Discord que tu cuenta de Epic está vinculada." }
          ],
          tip: "⚠️ <strong>Error común:</strong> Asegúrate de iniciar sesión en la cuenta correcta de Epic — la que realmente usas para jugar Fortnite."
        },
        {
          icon: "🎮",
          title: "Paso 3 — Inicia sesión en Pay2Slay",
          steps: [
            { title: "Vuelve a Pay2Slay", desc: "Regresa a <strong>pay2slay.cc</strong> y haz clic en <strong>Login with Discord</strong>." },
            { title: "Autoriza la aplicación", desc: "Discord te pedirá que autorices a Pay2Slay. Haz clic en <strong>Authorize</strong>." },
            { title: "Detección automática de Epic", desc: "Pay2Slay encuentra tu Epic ID automáticamente. Tu Dashboard mostrará <strong>Epic Linked: Yes</strong>." }
          ],
          tip: "🔍 <strong>Revisa tu Dashboard:</strong> Después de iniciar sesión, ve a la pestaña <strong>Dashboard</strong>. Busca \"Epic Linked\" — debería decir <strong>Yes</strong>."
        },
        {
          icon: "🍌",
          title: "Paso 4 — Configura tu billetera Banano",
          steps: [
            { title: "Obtén una billetera", desc: "Descarga <strong>Kalium</strong> (móvil) o usa <strong>vault.banano.cc</strong>. Tu dirección empieza con <strong>ban_</strong>." },
            { title: "Ve a la pestaña Wallet", desc: "En Pay2Slay, haz clic en <strong>Wallet</strong> y pega tu dirección <strong>ban_</strong>." },
            { title: "Guárdala", desc: "Haz clic en <strong>Update</strong>. Los pagos se enviarán automáticamente a esta dirección." }
          ],
          tip: "💡 <strong>¿Sin billetera?</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a> es la billetera Banano más popular."
        },
        {
          icon: "⚔️",
          title: "Paso 5 — Juega y gana",
          steps: [
            { title: "Juega Fortnite", desc: "Entra en cualquier partida pública. Cada eliminación es rastreada por la API de Fortnite." },
            { title: "Espera la acumulación", desc: "Las estadísticas aparecen unos minutos después del partido. Revisa el feed de <strong>Activity</strong>." },
            { title: "Recibe tu pago", desc: "Cada ciclo de liquidación, tus Banano se envían automáticamente a tu billetera." }
          ],
          tip: "⏱️ <strong>Tiempo:</strong> Las estadísticas suelen aparecer ~5 minutos después del partido."
        }
      ],
      faq: {
        title: "❓ Solución de problemas y FAQ",
        items: [
          { q: "Inicié sesión pero mi Epic no está vinculado", a: "Vuelve a nuestro servidor de Discord y completa la verificación de Yunite (Paso 2). Luego cierra sesión y vuelve a iniciarla." },
          { q: "Vinculé la cuenta Epic equivocada", a: "En Discord, usa el comando de desvinculación de Yunite, luego repite el proceso con la cuenta correcta." },
          { q: "Mis eliminaciones no aparecen", a: "Las estadísticas solo cuentan de partidas públicas. Verifica tu cuenta Epic en el Dashboard." },
          { q: "No he recibido mi pago de Banano", a: "Verifica tu dirección de billetera en la pestaña Wallet. Los pagos ocurren cada ciclo de liquidación." },
          { q: "¿Puedo cambiar mi dirección de billetera?", a: "Sí — ve a la pestaña Wallet y actualízala en cualquier momento." },
          { q: "¿Cuál es la tasa de pago por eliminación?", a: "La tasa depende del saldo del fondo y es establecida por los operadores." },
          { q: "Discord dice 'Necesitas verificar tu correo'", a: "Ve a Configuración de Discord → Mi Cuenta → verifica tu correo electrónico." }
        ]
      },
      hodl: {
        title: "🚀 Boost $JPMT HODL",
        intro: "Mantén tokens <strong>$JPMT</strong> en tu billetera Solana para obtener pagos de Banano aumentados por cada eliminación. ¡Cuanto más mantengas, mayor tu multiplicador!",
        howTitle: "Cómo funciona",
        howSteps: [
          { title: "Obtén $JPMT", desc: 'Compra $JPMT en <a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a> usando cualquier billetera Solana.' },
          { title: "Conecta tu billetera", desc: "En el Dashboard, pega tu dirección de billetera Solana y haz clic en <strong>Verify $JPMT Holdings</strong>." },
          { title: "Recibe el boost", desc: "Tu nivel y multiplicador se aplican automáticamente. ¡Re-verifica después de comprar más $JPMT!" }
        ],
        tiersTitle: "Niveles de Boost",
        tip: "💎 <strong>Consejo:</strong> El boost se basa en tu saldo al momento de la verificación. ¡Re-verifica después de comprar más $JPMT!",
        links: { buy: "Comprar $JPMT en Jupiter", website: "Sitio web JPMT", discord: "Discord JPMT" }
      }
    },

    pt: {
      intro: "Seu guia sherpa para configurar tudo e ganhar Banano por cada eliminação no Fortnite. Siga cada seção com cuidado — a vinculação de contas é onde a maioria das pessoas fica presa.",
      sections: [
        {
          icon: "🏠",
          title: "Passo 1 — Entre no servidor do Discord",
          steps: [
            { title: "Abra o link do convite", desc: "Clique no botão <strong>Entrar no Discord</strong> na página de login." },
            { title: "Aceite o convite", desc: "Se você não tem uma conta no Discord, crie uma primeiro. Use um e-mail real." },
            { title: "Verifique seu e-mail", desc: "O Discord pode pedir para verificar seu e-mail. Verifique sua caixa de entrada (e spam)." }
          ],
          tip: "🍌 <strong>Dica:</strong> Use a mesma conta do Discord em todos os lugares. Certifique-se de fazer login no Pay2Slay com a conta que está no nosso servidor."
        },
        {
          icon: "🔗",
          title: "Passo 2 — Vincule sua conta Epic Games (Yunite)",
          steps: [
            { title: "Encontre o canal de verificação", desc: "No nosso servidor Discord, procure o canal <strong>#verification</strong> ou <strong>#link-epic</strong>." },
            { title: "Clique no botão Link", desc: "Você verá uma mensagem do <strong>Yunite</strong> com um botão <strong>Link</strong>. Clique — uma janela do navegador abrirá." },
            { title: "Faça login na Epic Games", desc: "Entre na sua <strong>conta Epic Games</strong> (a mesma que você usa para jogar Fortnite). Autorize o acesso do Yunite." },
            { title: "Confirme a vinculação", desc: "O Yunite confirmará no Discord que sua conta Epic foi vinculada." }
          ],
          tip: "⚠️ <strong>Erro comum:</strong> Certifique-se de fazer login na conta Epic correta — aquela que você realmente usa para jogar Fortnite."
        },
        {
          icon: "🎮",
          title: "Passo 3 — Faça login no Pay2Slay",
          steps: [
            { title: "Volte ao Pay2Slay", desc: "Retorne a <strong>pay2slay.cc</strong> e clique em <strong>Login with Discord</strong>." },
            { title: "Autorize o aplicativo", desc: "O Discord pedirá para autorizar o Pay2Slay. Clique em <strong>Authorize</strong>." },
            { title: "Detecção automática do Epic", desc: "O Pay2Slay encontra seu Epic ID automaticamente. Seu Dashboard mostrará <strong>Epic Linked: Yes</strong>." }
          ],
          tip: "🔍 <strong>Verifique seu Dashboard:</strong> Depois de fazer login, vá para a aba <strong>Dashboard</strong>. Procure \"Epic Linked\" — deve dizer <strong>Yes</strong>."
        },
        {
          icon: "🍌",
          title: "Passo 4 — Configure sua carteira Banano",
          steps: [
            { title: "Obtenha uma carteira", desc: "Baixe o <strong>Kalium</strong> (celular) ou use <strong>vault.banano.cc</strong>. Seu endereço começa com <strong>ban_</strong>." },
            { title: "Vá para a aba Wallet", desc: "No Pay2Slay, clique na aba <strong>Wallet</strong> e cole seu endereço <strong>ban_</strong>." },
            { title: "Salve", desc: "Clique em <strong>Update</strong>. Os pagamentos serão enviados automaticamente para este endereço." }
          ],
          tip: "💡 <strong>Sem carteira?</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a> é a carteira Banano mais popular."
        },
        {
          icon: "⚔️",
          title: "Passo 5 — Jogue e ganhe",
          steps: [
            { title: "Jogue Fortnite", desc: "Entre em qualquer partida pública. Cada eliminação é rastreada pela API do Fortnite." },
            { title: "Aguarde o acúmulo", desc: "As estatísticas aparecem alguns minutos após a partida. Verifique o feed de <strong>Activity</strong>." },
            { title: "Receba seu pagamento", desc: "A cada ciclo de liquidação, seus Banano são enviados automaticamente para sua carteira." }
          ],
          tip: "⏱️ <strong>Tempo:</strong> As estatísticas geralmente aparecem ~5 minutos após a partida."
        }
      ],
      faq: {
        title: "❓ Solução de problemas e FAQ",
        items: [
          { q: "Fiz login mas meu Epic não está vinculado", a: "Volte ao nosso servidor Discord e complete a verificação do Yunite (Passo 2). Depois saia e entre novamente no Pay2Slay." },
          { q: "Vinculei a conta Epic errada", a: "No Discord, use o comando de desvinculação do Yunite, depois refaça o processo com a conta correta." },
          { q: "Minhas eliminações não aparecem", a: "As estatísticas contam apenas de partidas públicas. Verifique sua conta Epic no Dashboard." },
          { q: "Não recebi meu pagamento Banano", a: "Verifique seu endereço de carteira na aba Wallet. Os pagamentos acontecem a cada ciclo de liquidação." },
          { q: "Posso mudar meu endereço de carteira?", a: "Sim — vá para a aba Wallet e atualize a qualquer momento." },
          { q: "Qual é a taxa de pagamento por eliminação?", a: "A taxa depende do saldo do fundo e é definida pelos operadores." },
          { q: "Discord diz 'Você precisa verificar seu e-mail'", a: "Vá em Configurações do Discord → Minha Conta → verifique seu e-mail." }
        ]
      },
      hodl: {
        title: "🚀 Boost $JPMT HODL",
        intro: "Segure tokens <strong>$JPMT</strong> na sua carteira Solana para ganhar pagamentos de Banano aumentados por cada eliminação. Quanto mais você segurar, maior o multiplicador!",
        howTitle: "Como funciona",
        howSteps: [
          { title: "Obtenha $JPMT", desc: 'Compre $JPMT no <a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a> usando qualquer carteira Solana.' },
          { title: "Conecte sua carteira", desc: "No Dashboard, cole o endereço da sua carteira Solana e clique em <strong>Verify $JPMT Holdings</strong>." },
          { title: "Receba o boost", desc: "Seu nível e multiplicador são aplicados automaticamente. Re-verifique após comprar mais $JPMT!" }
        ],
        tiersTitle: "Níveis de Boost",
        tip: "💎 <strong>Dica:</strong> O boost é baseado no seu saldo no momento da verificação. Re-verifique após comprar mais $JPMT!",
        links: { buy: "Comprar $JPMT no Jupiter", website: "Site JPMT", discord: "Discord JPMT" }
      }
    },

    ja: {
      intro: "Fortniteでの各エリミネーションでBananoを稼ぐためのセットアップガイドです。各セクションを注意深く進めてください — アカウントのリンク部分でつまずく人が多いです。",
      sections: [
        {
          icon: "🏠",
          title: "ステップ1 — Discordサーバーに参加",
          steps: [
            { title: "招待リンクを開く", desc: "ログインページの<strong>Discordに参加</strong>ボタンをクリックしてください。" },
            { title: "招待を承認", desc: "Discordアカウントがまだない場合は、まず作成してください。認証可能な本物のメールアドレスを使用してください。" },
            { title: "メールを確認", desc: "Discordがメール確認を求める場合があります。受信トレイ（とスパムフォルダ）を確認してください。" }
          ],
          tip: "🍌 <strong>ヒント：</strong>どこでも同じDiscordアカウントを使用してください。Pay2Slayにはサーバーにいるのと同じアカウントでログインしてください。"
        },
        {
          icon: "🔗",
          title: "ステップ2 — Epic Gamesアカウントをリンク（Yunite）",
          steps: [
            { title: "認証チャンネルを見つける", desc: "Discordサーバーで<strong>#verification</strong>または<strong>#link-epic</strong>チャンネルを探してください。" },
            { title: "Linkボタンをクリック", desc: "<strong>Yunite</strong>からのメッセージに<strong>Link</strong>ボタンがあります。クリックするとブラウザが開きます。" },
            { title: "Epic Gamesにサインイン", desc: "<strong>Epic Gamesアカウント</strong>にログインしてください（Fortniteをプレイしているのと同じアカウント）。Yuniteのアクセスを許可してください。" },
            { title: "リンクを確認", desc: "承認後、YuniteがDiscordでEpicアカウントのリンクを確認します。" }
          ],
          tip: "⚠️ <strong>よくある間違い：</strong>正しいEpicアカウントにサインインしていることを確認してください — 実際にFortniteをプレイしているアカウントです。"
        },
        {
          icon: "🎮",
          title: "ステップ3 — Pay2Slayにログイン",
          steps: [
            { title: "Pay2Slayに戻る", desc: "<strong>pay2slay.cc</strong>に戻り、<strong>Login with Discord</strong>をクリックしてください。" },
            { title: "アプリを承認", desc: "DiscordがPay2Slayの承認を求めます。<strong>Authorize</strong>をクリックしてください。" },
            { title: "Epic自動検出", desc: "Pay2SlayはYuniteを通じてEpic IDを自動的に検出します。ダッシュボードに<strong>Epic Linked: Yes</strong>と表示されます。" }
          ],
          tip: "🔍 <strong>ダッシュボードを確認：</strong>ログイン後、<strong>Dashboard</strong>タブに移動してください。「Epic Linked」が<strong>Yes</strong>であることを確認してください。"
        },
        {
          icon: "🍌",
          title: "ステップ4 — Bananoウォレットを設定",
          steps: [
            { title: "ウォレットを入手", desc: "<strong>Kalium</strong>（モバイル）をダウンロードするか、<strong>vault.banano.cc</strong>を使用してください。アドレスは<strong>ban_</strong>で始まります。" },
            { title: "Walletタブに移動", desc: "Pay2Slayで<strong>Wallet</strong>タブをクリックし、<strong>ban_</strong>アドレスを貼り付けてください。" },
            { title: "保存", desc: "<strong>Update</strong>をクリックしてください。支払いは自動的にこのアドレスに送信されます。" }
          ],
          tip: "💡 <strong>ウォレットがない？</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a>は最も人気のあるBananoウォレットです。"
        },
        {
          icon: "⚔️",
          title: "ステップ5 — プレイして稼ぐ",
          steps: [
            { title: "Fortniteをプレイ", desc: "任意のパブリックマッチに参加してください。すべてのエリミネーションはFortnite APIで追跡されます。" },
            { title: "計上を待つ", desc: "マッチ終了後数分で統計が表示されます。<strong>Activity</strong>フィードで確認してください。" },
            { title: "支払いを受け取る", desc: "各決済サイクルで、蓄積されたBananoが自動的にウォレットに送信されます。" }
          ],
          tip: "⏱️ <strong>タイミング：</strong>統計は通常マッチ終了後約5分で表示されます。"
        }
      ],
      faq: {
        title: "❓ トラブルシューティングとFAQ",
        items: [
          { q: "ログインしたがEpicがリンクされていない", a: "Discordサーバーに戻り、Yunite認証（ステップ2）を完了してください。その後Pay2Slayからログアウトして再ログインしてください。" },
          { q: "間違ったEpicアカウントをリンクした", a: "Discordサーバーで Yuniteのリンク解除コマンドを使用し、正しいアカウントでリンクし直してください。" },
          { q: "キルが表示されない", a: "統計はパブリックマッチのみカウントされます。DashboardでEpicアカウントを確認してください。" },
          { q: "Banano支払いを受け取っていない", a: "Walletタブでウォレットアドレスを確認してください。支払いは各決済サイクルで行われます。" },
          { q: "ウォレットアドレスを変更できますか？", a: "はい — Walletタブでいつでも更新できます。" },
          { q: "キルあたりの支払い率は？", a: "レートはファンドの残高に依存し、運営者が設定します。" },
          { q: "Discordが「メールの確認が必要」と表示する", a: "Discord設定 → マイアカウント → メールアドレスを確認してください。" }
        ]
      },
      hodl: {
        title: "🚀 $JPMT HODLブースト",
        intro: "Solanaウォレットに<strong>$JPMT</strong>トークンを保持して、キルごとのBanano支払いをブーストしましょう。多く保持するほど、倍率が高くなります！",
        howTitle: "仕組み",
        howSteps: [
          { title: "$JPMTを取得", desc: '<a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a>で任意のSolanaウォレットを使って$JPMTを購入してください。' },
          { title: "ウォレットを接続", desc: "DashboardでSolanaウォレットアドレスを貼り付け、<strong>Verify $JPMT Holdings</strong>をクリックしてください。" },
          { title: "ブーストを受け取る", desc: "ティアと倍率は自動的に適用されます。$JPMTを追加購入した後に再確認してください！" }
        ],
        tiersTitle: "ブーストティア",
        tip: "💎 <strong>ヒント：</strong>ブーストは確認時の残高に基づきます。$JPMTを追加購入した後に再確認してください！",
        links: { buy: "Jupiterで$JPMTを購入", website: "JPMTウェブサイト", discord: "JPMT Discord" }
      }
    },

    fr: {
      intro: "Votre guide sherpa pour tout configurer et gagner du Banano pour chaque élimination sur Fortnite. Suivez chaque section attentivement — la liaison des comptes est l'étape où la plupart des gens bloquent.",
      sections: [
        {
          icon: "🏠",
          title: "Étape 1 — Rejoindre le serveur Discord",
          steps: [
            { title: "Ouvrir le lien d'invitation", desc: "Cliquez sur le bouton <strong>Rejoindre Discord</strong> sur la page de connexion." },
            { title: "Accepter l'invitation", desc: "Si vous n'avez pas de compte Discord, créez-en un d'abord. Utilisez un vrai e-mail que vous pouvez vérifier." },
            { title: "Vérifier votre e-mail", desc: "Discord peut vous demander de vérifier votre e-mail. Vérifiez votre boîte de réception (et le dossier spam)." }
          ],
          tip: "🍌 <strong>Astuce :</strong> Utilisez le même compte Discord partout. Assurez-vous de vous connecter à Pay2Slay avec le compte qui est sur notre serveur."
        },
        {
          icon: "🔗",
          title: "Étape 2 — Lier votre compte Epic Games (Yunite)",
          steps: [
            { title: "Trouver le canal de vérification", desc: "Sur notre serveur Discord, cherchez le canal <strong>#verification</strong> ou <strong>#link-epic</strong>." },
            { title: "Cliquer sur le bouton Link", desc: "Vous verrez un message de <strong>Yunite</strong> avec un bouton <strong>Link</strong>. Cliquez — une fenêtre de navigateur s'ouvrira." },
            { title: "Se connecter à Epic Games", desc: "Connectez-vous à votre <strong>compte Epic Games</strong> (celui avec lequel vous jouez à Fortnite). Autorisez l'accès de Yunite." },
            { title: "Confirmer la liaison", desc: "Yunite confirmera dans Discord que votre compte Epic est lié. Vous verrez votre nom d'affichage Epic." }
          ],
          tip: "⚠️ <strong>Erreur fréquente :</strong> Assurez-vous de vous connecter au bon compte Epic — celui que vous utilisez réellement pour jouer à Fortnite."
        },
        {
          icon: "🎮",
          title: "Étape 3 — Se connecter à Pay2Slay",
          steps: [
            { title: "Retourner sur Pay2Slay", desc: "Retournez sur <strong>pay2slay.cc</strong> et cliquez sur <strong>Login with Discord</strong>." },
            { title: "Autoriser l'application", desc: "Discord vous demandera d'autoriser Pay2Slay. Cliquez sur <strong>Authorize</strong>." },
            { title: "Détection automatique d'Epic", desc: "Pay2Slay trouve automatiquement votre Epic ID via Yunite. Votre Dashboard affichera <strong>Epic Linked: Yes</strong>." }
          ],
          tip: "🔍 <strong>Vérifiez votre Dashboard :</strong> Après la connexion, allez dans l'onglet <strong>Dashboard</strong>. Cherchez \"Epic Linked\" — il devrait indiquer <strong>Yes</strong>."
        },
        {
          icon: "🍌",
          title: "Étape 4 — Configurer votre portefeuille Banano",
          steps: [
            { title: "Obtenir un portefeuille", desc: "Téléchargez <strong>Kalium</strong> (mobile) ou utilisez <strong>vault.banano.cc</strong>. Votre adresse commence par <strong>ban_</strong>." },
            { title: "Aller dans l'onglet Wallet", desc: "Dans Pay2Slay, cliquez sur l'onglet <strong>Wallet</strong> et collez votre adresse <strong>ban_</strong>." },
            { title: "Enregistrer", desc: "Cliquez sur <strong>Update</strong>. Les paiements seront envoyés automatiquement à cette adresse." }
          ],
          tip: "💡 <strong>Pas de portefeuille ?</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a> est le portefeuille Banano le plus populaire."
        },
        {
          icon: "⚔️",
          title: "Étape 5 — Jouez et gagnez",
          steps: [
            { title: "Jouez à Fortnite", desc: "Lancez n'importe quelle partie publique. Chaque élimination est suivie par l'API Fortnite." },
            { title: "Attendez l'accumulation", desc: "Les statistiques apparaissent quelques minutes après la partie. Consultez le flux <strong>Activity</strong>." },
            { title: "Recevez votre paiement", desc: "À chaque cycle de règlement, vos Banano sont envoyés automatiquement à votre portefeuille." }
          ],
          tip: "⏱️ <strong>Timing :</strong> Les statistiques apparaissent généralement ~5 minutes après la fin de la partie."
        }
      ],
      faq: {
        title: "❓ Dépannage et FAQ",
        items: [
          { q: "Je me suis connecté mais mon Epic n'est pas lié", a: "Retournez sur notre serveur Discord et complétez la vérification Yunite (Étape 2). Ensuite déconnectez-vous et reconnectez-vous à Pay2Slay." },
          { q: "J'ai lié le mauvais compte Epic", a: "Sur Discord, utilisez la commande de déliaison de Yunite, puis refaites le processus avec le bon compte." },
          { q: "Mes éliminations n'apparaissent pas", a: "Les statistiques ne comptent que les parties publiques. Vérifiez votre compte Epic dans le Dashboard." },
          { q: "Je n'ai pas reçu mon paiement Banano", a: "Vérifiez votre adresse dans l'onglet Wallet. Les paiements ont lieu à chaque cycle de règlement." },
          { q: "Puis-je changer mon adresse de portefeuille ?", a: "Oui — allez dans l'onglet Wallet et mettez-la à jour à tout moment." },
          { q: "Quel est le taux de paiement par élimination ?", a: "Le taux dépend du solde du fonds et est fixé par les opérateurs." },
          { q: "Discord dit 'Vous devez vérifier votre e-mail'", a: "Allez dans Paramètres Discord → Mon Compte → vérifiez votre adresse e-mail." }
        ]
      },
      hodl: {
        title: "🚀 Boost $JPMT HODL",
        intro: "Détenez des tokens <strong>$JPMT</strong> dans votre portefeuille Solana pour obtenir des paiements Banano augmentés à chaque élimination. Plus vous détenez, plus votre multiplicateur est élevé !",
        howTitle: "Comment ça marche",
        howSteps: [
          { title: "Obtenez des $JPMT", desc: 'Achetez des $JPMT sur <a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a> avec n\'importe quel portefeuille Solana.' },
          { title: "Connectez votre portefeuille", desc: "Sur le Dashboard, collez votre adresse de portefeuille Solana et cliquez sur <strong>Verify $JPMT Holdings</strong>." },
          { title: "Obtenez le boost", desc: "Votre niveau et multiplicateur s'appliquent automatiquement. Re-vérifiez après avoir acheté plus de $JPMT !" }
        ],
        tiersTitle: "Niveaux de Boost",
        tip: "💎 <strong>Astuce :</strong> Le boost est basé sur votre solde au moment de la vérification. Re-vérifiez après avoir acheté plus de $JPMT !",
        links: { buy: "Acheter $JPMT sur Jupiter", website: "Site web JPMT", discord: "Discord JPMT" }
      }
    },

    de: {
      intro: "Dein Sherpa-Guide für die Einrichtung und das Verdienen von Banano für jede Fortnite-Eliminierung. Folge jedem Abschnitt sorgfältig — die Kontoverknüpfung ist der Punkt, an dem die meisten Leute hängen bleiben.",
      sections: [
        {
          icon: "🏠",
          title: "Schritt 1 — Dem Discord-Server beitreten",
          steps: [
            { title: "Einladungslink öffnen", desc: "Klicke auf der Login-Seite auf <strong>Discord beitreten</strong>." },
            { title: "Einladung annehmen", desc: "Falls du noch keinen Discord-Account hast, erstelle zuerst einen. Verwende eine echte E-Mail-Adresse." },
            { title: "E-Mail bestätigen", desc: "Discord kann dich auffordern, deine E-Mail zu bestätigen. Überprüfe deinen Posteingang (und Spam-Ordner)." }
          ],
          tip: "🍌 <strong>Tipp:</strong> Verwende überall denselben Discord-Account. Stelle sicher, dass du dich bei Pay2Slay mit dem Account anmeldest, der auf unserem Server ist."
        },
        {
          icon: "🔗",
          title: "Schritt 2 — Epic Games-Konto verknüpfen (Yunite)",
          steps: [
            { title: "Verifizierungskanal finden", desc: "Suche auf unserem Discord-Server den Kanal <strong>#verification</strong> oder <strong>#link-epic</strong>." },
            { title: "Link-Button klicken", desc: "Du siehst eine Nachricht von <strong>Yunite</strong> mit einem <strong>Link</strong>-Button. Klick darauf — ein Browserfenster öffnet sich." },
            { title: "Bei Epic Games anmelden", desc: "Melde dich bei deinem <strong>Epic Games-Konto</strong> an (dasselbe, mit dem du Fortnite spielst). Autorisiere den Zugriff von Yunite." },
            { title: "Verknüpfung bestätigen", desc: "Yunite bestätigt in Discord, dass dein Epic-Konto verknüpft ist. Du siehst deinen Epic-Anzeigenamen." }
          ],
          tip: "⚠️ <strong>Häufiger Fehler:</strong> Stelle sicher, dass du dich beim richtigen Epic-Konto anmeldest — dem, mit dem du tatsächlich Fortnite spielst."
        },
        {
          icon: "🎮",
          title: "Schritt 3 — Bei Pay2Slay anmelden",
          steps: [
            { title: "Zurück zu Pay2Slay", desc: "Gehe zurück zu <strong>pay2slay.cc</strong> und klicke auf <strong>Login with Discord</strong>." },
            { title: "App autorisieren", desc: "Discord bittet dich, Pay2Slay zu autorisieren. Klicke auf <strong>Authorize</strong>." },
            { title: "Automatische Epic-Erkennung", desc: "Pay2Slay findet deine Epic ID automatisch über Yunite. Dein Dashboard zeigt <strong>Epic Linked: Yes</strong>." }
          ],
          tip: "🔍 <strong>Dashboard prüfen:</strong> Nach dem Login gehe zum <strong>Dashboard</strong>-Tab. Suche \"Epic Linked\" — es sollte <strong>Yes</strong> anzeigen."
        },
        {
          icon: "🍌",
          title: "Schritt 4 — Banano-Wallet einrichten",
          steps: [
            { title: "Wallet besorgen", desc: "Lade <strong>Kalium</strong> (Mobil) herunter oder nutze <strong>vault.banano.cc</strong>. Deine Adresse beginnt mit <strong>ban_</strong>." },
            { title: "Zum Wallet-Tab", desc: "Klicke in Pay2Slay auf den <strong>Wallet</strong>-Tab und füge deine <strong>ban_</strong>-Adresse ein." },
            { title: "Speichern", desc: "Klicke auf <strong>Update</strong>. Auszahlungen werden automatisch an diese Adresse gesendet." }
          ],
          tip: "💡 <strong>Kein Wallet?</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a> ist die beliebteste Banano-Wallet."
        },
        {
          icon: "⚔️",
          title: "Schritt 5 — Spielen und verdienen",
          steps: [
            { title: "Fortnite spielen", desc: "Starte ein beliebiges öffentliches Match. Jede Eliminierung wird von der Fortnite-API verfolgt." },
            { title: "Auf Anrechnung warten", desc: "Statistiken erscheinen einige Minuten nach dem Match. Überprüfe den <strong>Activity</strong>-Feed." },
            { title: "Auszahlung erhalten", desc: "In jedem Abrechnungszyklus werden deine Banano automatisch an dein Wallet gesendet." }
          ],
          tip: "⏱️ <strong>Timing:</strong> Statistiken erscheinen normalerweise ~5 Minuten nach Spielende."
        }
      ],
      faq: {
        title: "❓ Fehlerbehebung und FAQ",
        items: [
          { q: "Ich habe mich angemeldet, aber mein Epic ist nicht verknüpft", a: "Gehe zurück zu unserem Discord-Server und schließe die Yunite-Verifizierung ab (Schritt 2). Dann melde dich ab und wieder an." },
          { q: "Ich habe das falsche Epic-Konto verknüpft", a: "Verwende auf Discord den Yunite-Entkoppeln-Befehl und verknüpfe dann das richtige Konto." },
          { q: "Meine Eliminierungen werden nicht angezeigt", a: "Statistiken zählen nur aus öffentlichen Matches. Überprüfe dein Epic-Konto im Dashboard." },
          { q: "Ich habe meine Banano-Auszahlung nicht erhalten", a: "Überprüfe deine Wallet-Adresse im Wallet-Tab. Auszahlungen erfolgen in jedem Abrechnungszyklus." },
          { q: "Kann ich meine Wallet-Adresse ändern?", a: "Ja — gehe zum Wallet-Tab und aktualisiere sie jederzeit." },
          { q: "Wie hoch ist die Auszahlungsrate pro Eliminierung?", a: "Die Rate hängt vom Fondsguthaben ab und wird von den Betreibern festgelegt." },
          { q: "Discord sagt 'Du musst deine E-Mail bestätigen'", a: "Gehe zu Discord-Einstellungen → Mein Konto → bestätige deine E-Mail-Adresse." }
        ]
      },
      hodl: {
        title: "🚀 $JPMT HODL-Boost",
        intro: "Halte <strong>$JPMT</strong>-Tokens in deiner Solana-Wallet, um erhöhte Banano-Auszahlungen für jede Eliminierung zu erhalten. Je mehr du hältst, desto höher dein Multiplikator!",
        howTitle: "So funktioniert's",
        howSteps: [
          { title: "$JPMT kaufen", desc: 'Kaufe $JPMT auf <a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a> mit jeder Solana-Wallet.' },
          { title: "Wallet verbinden", desc: "Im Dashboard füge deine Solana-Wallet-Adresse ein und klicke auf <strong>Verify $JPMT Holdings</strong>." },
          { title: "Boost erhalten", desc: "Dein Tier und Multiplikator werden automatisch angewendet. Nach dem Kauf von mehr $JPMT erneut verifizieren!" }
        ],
        tiersTitle: "Boost-Stufen",
        tip: "💎 <strong>Tipp:</strong> Der Boost basiert auf deinem Guthaben zum Zeitpunkt der Verifizierung. Nach dem Kauf von mehr $JPMT erneut verifizieren!",
        links: { buy: "$JPMT auf Jupiter kaufen", website: "JPMT-Website", discord: "JPMT Discord" }
      }
    },

    zh: {
      intro: "这是您设置账户并通过Fortnite每次淘汰赚取Banano的向导。请仔细按照每个部分操作——账户关联是大多数人遇到困难的地方。",
      sections: [
        {
          icon: "🏠",
          title: "第1步 — 加入Discord服务器",
          steps: [
            { title: "打开邀请链接", desc: "在登录页面点击<strong>加入Discord</strong>按钮。" },
            { title: "接受邀请", desc: "如果您还没有Discord账户，请先创建一个。使用可以验证的真实电子邮件。" },
            { title: "验证电子邮件", desc: "Discord可能会要求您验证电子邮件。检查您的收件箱（和垃圾邮件文件夹）。" }
          ],
          tip: "🍌 <strong>提示：</strong>在所有地方使用同一个Discord账户。确保您使用我们服务器中的同一账户登录Pay2Slay。"
        },
        {
          icon: "🔗",
          title: "第2步 — 关联Epic Games账户（Yunite）",
          steps: [
            { title: "找到验证频道", desc: "在我们的Discord服务器中，寻找<strong>#verification</strong>或<strong>#link-epic</strong>频道。" },
            { title: "点击Link按钮", desc: "您会看到<strong>Yunite</strong>发送的消息，带有<strong>Link</strong>按钮。点击后浏览器窗口将打开。" },
            { title: "登录Epic Games", desc: "登录您的<strong>Epic Games账户</strong>（您用来玩Fortnite的那个）。授权Yunite访问。" },
            { title: "确认关联", desc: "授权后，Yunite会在Discord确认您的Epic账户已关联。您会看到您的Epic显示名称。" }
          ],
          tip: "⚠️ <strong>常见错误：</strong>确保您登录的是正确的Epic账户——您实际用来玩Fortnite的那个。"
        },
        {
          icon: "🎮",
          title: "第3步 — 登录Pay2Slay",
          steps: [
            { title: "返回Pay2Slay", desc: "回到<strong>pay2slay.cc</strong>并点击<strong>Login with Discord</strong>。" },
            { title: "授权应用", desc: "Discord会要求您授权Pay2Slay。点击<strong>Authorize</strong>。" },
            { title: "自动检测Epic", desc: "Pay2Slay通过Yunite自动找到您的Epic ID。您的Dashboard将显示<strong>Epic Linked: Yes</strong>。" }
          ],
          tip: "🔍 <strong>检查Dashboard：</strong>登录后，转到<strong>Dashboard</strong>标签。查找\"Epic Linked\"——应该显示<strong>Yes</strong>。"
        },
        {
          icon: "🍌",
          title: "第4步 — 设置Banano钱包",
          steps: [
            { title: "获取钱包", desc: "下载<strong>Kalium</strong>（手机端）或使用<strong>vault.banano.cc</strong>。您的地址以<strong>ban_</strong>开头。" },
            { title: "前往Wallet标签", desc: "在Pay2Slay中，点击<strong>Wallet</strong>标签并粘贴您的<strong>ban_</strong>地址。" },
            { title: "保存", desc: "点击<strong>Update</strong>。付款将自动发送到此地址。" }
          ],
          tip: "💡 <strong>还没有钱包？</strong> <a href=\"https://kalium.banano.cc/\" target=\"_blank\">Kalium</a>是最受欢迎的Banano钱包。"
        },
        {
          icon: "⚔️",
          title: "第5步 — 玩游戏赚钱",
          steps: [
            { title: "玩Fortnite", desc: "加入任何公开比赛。您的每次淘汰都会被Fortnite API追踪。" },
            { title: "等待累计", desc: "比赛结束后几分钟统计数据就会出现。查看<strong>Activity</strong>动态。" },
            { title: "接收付款", desc: "每个结算周期，您累计的Banano会自动发送到您的钱包。" }
          ],
          tip: "⏱️ <strong>时间：</strong>统计数据通常在比赛结束后约5分钟出现。"
        }
      ],
      faq: {
        title: "❓ 故障排除和常见问题",
        items: [
          { q: "我已登录但Epic账户未关联", a: "返回我们的Discord服务器完成Yunite验证（第2步）。然后退出Pay2Slay并重新登录。" },
          { q: "我关联了错误的Epic账户", a: "在Discord使用Yunite的取消关联命令，然后用正确的账户重新关联。" },
          { q: "我的淘汰数没有显示", a: "统计数据仅计算公开比赛。在Dashboard检查您的Epic账户。" },
          { q: "我没有收到Banano付款", a: "在Wallet标签中检查您的钱包地址。付款在每个结算周期进行。" },
          { q: "我可以更改钱包地址吗？", a: "可以——前往Wallet标签随时更新。" },
          { q: "每次淘汰的支付率是多少？", a: "费率取决于资金余额，由运营者设定。" },
          { q: "Discord说'您需要验证电子邮件'", a: "前往Discord设置 → 我的账户 → 验证您的电子邮件地址。" }
        ]
      },
      hodl: {
        title: "🚀 $JPMT HODL加速",
        intro: "在您的Solana钱包中持有<strong>$JPMT</strong>代币，以获得每次淘汰更高的Banano支付。持有越多，倍率越高！",
        howTitle: "如何运作",
        howSteps: [
          { title: "获取$JPMT", desc: '使用任何Solana钱包在<a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank">Jupiter</a>上购买$JPMT。' },
          { title: "连接钱包", desc: "在Dashboard中，粘贴您的Solana钱包地址并点击<strong>Verify $JPMT Holdings</strong>。" },
          { title: "获得加速", desc: "您的等级和倍率会自动应用。购买更多$JPMT后重新验证！" }
        ],
        tiersTitle: "加速等级",
        tip: "💎 <strong>提示：</strong>加速基于验证时的余额。购买更多$JPMT后重新验证以升级！",
        links: { buy: "在Jupiter购买$JPMT", website: "JPMT网站", discord: "JPMT Discord" }
      }
    }
  };

  // ── Renderer ──────────────────────────────────────────
  function renderHelp(lang) {
    var data = HELP[lang] || HELP.en;
    var html = '';

    // Intro
    html += '<div class="help-section"><p style="color:var(--text-muted);font-size:14px;line-height:1.6;">' + data.intro + '</p></div>';

    // Sections
    for (var i = 0; i < data.sections.length; i++) {
      var sec = data.sections[i];
      html += '<div class="help-section">';
      html += '<h3><span class="sherpa-icon">' + sec.icon + '</span> ' + sec.title + '</h3>';
      html += '<div class="help-steps">';
      for (var j = 0; j < sec.steps.length; j++) {
        var step = sec.steps[j];
        html += '<div class="help-step">';
        html += '<div class="help-step-num">' + (j + 1) + '</div>';
        html += '<div class="help-step-body"><strong>' + step.title + '</strong><p>' + step.desc + '</p></div>';
        html += '</div>';
      }
      html += '</div>';
      if (sec.tip) {
        html += '<div class="help-tip">' + sec.tip + '</div>';
      }
      html += '</div>';
    }

    // FAQ
    if (data.faq) {
      html += '<div class="help-section">';
      html += '<h3>' + data.faq.title + '</h3>';
      html += '<div class="help-faq">';
      for (var k = 0; k < data.faq.items.length; k++) {
        var faq = data.faq.items[k];
        html += '<details><summary>' + faq.q + '</summary>';
        html += '<div class="faq-answer">' + faq.a + '</div></details>';
      }
      html += '</div></div>';
    }

    // HODL Boost
    if (data.hodl) {
      var h = data.hodl;
      html += '<div class="help-section hodl-boost-card">';
      html += '<h3>' + h.title + '</h3>';
      html += '<p style="color:var(--text-muted);font-size:14px;line-height:1.6;">' + h.intro + '</p>';
      html += '<h4 style="margin-top:16px;">' + h.howTitle + '</h4>';
      html += '<div class="help-steps">';
      for (var m = 0; m < h.howSteps.length; m++) {
        var hs = h.howSteps[m];
        html += '<div class="help-step">';
        html += '<div class="help-step-num">' + (m + 1) + '</div>';
        html += '<div class="help-step-body"><strong>' + hs.title + '</strong><p>' + hs.desc + '</p></div>';
        html += '</div>';
      }
      html += '</div>';
      html += '<h4 style="margin-top:16px;">' + h.tiersTitle + '</h4>';
      html += '<table class="hodl-tier-table"><thead><tr><th>Tier</th><th>Badge</th><th>Tokens</th><th>Boost</th></tr></thead><tbody>';
      var tiers = [
        { name: "Bronze HODLr", badge: "🥉", min: "10,000", mult: "1.10×" },
        { name: "Silver HODLr", badge: "🥈", min: "100,000", mult: "1.20×" },
        { name: "Gold HODLr", badge: "🥇", min: "1,000,000", mult: "1.35×" },
        { name: "Diamond HODLr", badge: "💎", min: "10,000,000", mult: "1.50×" },
        { name: "Whale HODLr", badge: "🐋", min: "100,000,000", mult: "1.75×" }
      ];
      for (var t = 0; t < tiers.length; t++) {
        html += '<tr><td>' + tiers[t].name + '</td><td>' + tiers[t].badge + '</td><td>' + tiers[t].min + '</td><td>' + tiers[t].mult + '</td></tr>';
      }
      html += '</tbody></table>';
      if (h.tip) {
        html += '<div class="help-tip">' + h.tip + '</div>';
      }
      html += '<div class="hodl-links" style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">';
      html += '<a href="https://jup.ag/tokens/7ErxzRN1hpyMZC8gps7ANZFTGgeDG7cFmVZcMfE6oGrd" target="_blank" class="btn-sol">' + h.links.buy + '</a>';
      html += '<a href="https://jpmt.cc/" target="_blank" class="btn-jpmt">' + h.links.website + '</a>';
      html += '<a href="https://discord.gg/ukg7vgjQ48" target="_blank" class="btn-jpmt">' + h.links.discord + '</a>';
      html += '</div>';
      html += '</div>';
    }

    var container = document.getElementById('help-content');
    if (container) container.innerHTML = html;
  }

  // ── Language Switcher ─────────────────────────────────
  function setupHelpLangSwitcher() {
    var buttons = document.querySelectorAll('.help-lang');
    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        buttons.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        renderHelp(btn.dataset.lang);
      });
    });
  }

  // ── Init on DOM ready ─────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      setupHelpLangSwitcher();
      renderHelp('en');
    });
  } else {
    setupHelpLangSwitcher();
    renderHelp('en');
  }
})();
