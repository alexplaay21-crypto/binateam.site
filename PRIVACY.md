<!-- Generated from app/src/main/java/com/sboard/app/core/legal/LegalDocs.kt — edit there and regenerate. -->

# sBoard — Политика конфиденциальности / Privacy Policy

## Политика конфиденциальности

_Редакция от 12 ноября 2026 г._

### Коротко

sBoard — клавиатура и менеджер паролей sPass. У разработчиков нет своего сервера: приложение не создаёт аккаунт у нас, не собирает статистику и не передаёт нам то, что вы печатаете. Почти всё работает на телефоне. Ниже перечислены все случаи, когда данные уходят во внешние сервисы, — каждый из них вы включаете сами.

### Что остаётся на телефоне

• Всё, что вы печатаете на клавиатуре. Набранный текст не сохраняется и никуда не отправляется.
• Выученные слова, личный словарь, быстрые фразы, история буфера обмена (текст и фото), статистика набора — в памяти приложения. В полях паролей обучение выключено. Когда клавиатура открывается, она читает системный буфер обмена, чтобы показать только что скопированное; содержимое остаётся на телефоне. Если включить «Скриншоты в буфере», клавиатура замечает новые снимки экрана и копирует их в свой буфер; другие фото она не читает.
• Записи sPass (пароли, карты, документы, коды 2FA, ключи доступа) — в базе, зашифрованной AES-256-GCM ключом, который выводится из мастер-пароля (Argon2id). Без мастер-пароля, ключа восстановления или настроенного способа восстановления данные расшифровать нельзя — в том числе нам.
• Сохранённые личные данные для подсказок (телефон, e-mail, адрес) — зашифрованы на устройстве и сохраняются только после вашего подтверждения.
• Подсказки автозаполнения до разблокировки: названия и логины аккаунтов (без паролей и кодов) — зашифрованы ключом Android Keystore, чтобы сразу показывать подходящие аккаунты. Выключается в Профиль → «Вход и восстановление».
• Сохранение из форм: после отправки формы входа, банковской карты или личных данных Android передаёт sBoard введённые значения; они хранятся в памяти не дольше 5 минут и попадают в sPass только после вашего подтверждения.
• Фото фона клавиатуры — копия внутри приложения.

### Перевод

Когда открыта панель перевода, текст из поля отправляется сервису, выбранному в настройках переводчика: Google Translate (по умолчанию) или MyMemory — без ключа; Google Cloud Translation, Microsoft Translator, DeepL или Yandex Translate — с вашим ключом API; LibreTranslate — на сервер по адресу, который вы указали. Если Google Translate или MyMemory недоступен, текст отправляется второму из них; сервис с вашим ключом или сервером никогда не заменяется другим. Ключи и адрес хранятся только на телефоне и передаются только выбранному сервису. Эти компании и владельцы серверов обрабатывают текст по своим правилам. Последние переводы хранятся только в оперативной памяти и стираются при закрытии приложения. Не используйте перевод для конфиденциального текста.

Язык интерфейса: если для выбранного языка в приложении нет перевода каких-то надписей, эти надписи приложения (не ваши данные и не набранный текст) один раз переводятся через Google Translate и сохраняются на телефоне.

### Голосовой ввод

Распознавание речи выполняет сервис Android на вашем телефоне (обычно от Google). Если на устройстве есть офлайн-модель, sBoard выбирает её — тогда звук не покидает телефон. Иначе звук обрабатывает этот сервис по своим правилам. sBoard не записывает и не хранит звук.

### Другие функции с интернетом

• GIF: поисковый запрос отправляется в GIPHY, когда вы открываете вкладку GIF.
• Курсы валют для конвертера загружаются раз в сутки с open.er-api.com (без ваших данных).
• Проверка утечек: в Have I Been Pwned уходят только первые 5 символов SHA-1-хэша пароля (k-анонимность), сам пароль не передаётся; проверка e-mail отправляет адрес в XposedOrNot — только по вашей кнопке.
• Значки сайтов: если включено, приложение запрашивает значок (favicon) у сайта сохранённой записи. Сайт видит только запрос значка.
• Сканирование паспорта (строки с символами «<») распознаёт текст прямо с камеры на телефоне (Google ML Kit); кадры не сохраняются и не отправляются, ML Kit может передавать Google обезличенные технические сведения о работе библиотеки.

### Облачные копии и вход

Синхронизация выключена, пока вы не подключите своё облако: Google Drive, Dropbox или WebDAV. Копия шифруется на телефоне до отправки; облако хранит только зашифрованный файл и служебные сведения (размер, время изменения). Вход выполняется через официальные механизмы провайдеров (Google Sign-In, OAuth 2.0 с PKCE). Токены доступа хранятся на телефоне в зашифрованном виде. Внутри зашифрованной копии также лежат ваши настройки, выученные слова и данные подключения других облаков (токен Dropbox; адрес, логин и пароль приложения WebDAV), чтобы на новом телефоне всё подключилось само. Отключить облако можно в любой момент — локальные токены удаляются; доступ у самого провайдера sBoard не отзывает, поэтому копия в облаке сохраняется. Полностью закрыть доступ можно в настройках аккаунта провайдера. Для профиля приложение показывает фото основного аккаунта Google или Dropbox: адрес фото приходит вместе с именем и почтой аккаунта, само фото один раз загружается у Google или Dropbox и хранится только на телефоне. «Удалить все данные» удаляет копию sPass во всех подключённых облаках и sPass на телефоне. Когда устройство отключают на другом телефоне, при следующей синхронизации оно удаляет sPass, забывает вход во все облака и отзывает свой токен Dropbox у Dropbox.

### Восстановление доступа

Хранилище открывает мастер-пароль или ключ восстановления (Recovery Key); ни тот, ни другой никогда не хранятся в открытом виде — ни на телефоне, ни в облаке. Если вы забыли оба, помогают контрольные вопросы: из ответов выводится ключ (Argon2id), который открывает хранилище только вместе со второй частью — она хранится на телефоне под защитой блокировки экрана и в зашифрованной копии в вашем облаке. Одни ответы или один вход в облако хранилище не открывают. Прежний режим «Восстановление через аккаунт облака» убран: при обновлении его ключ удаляется из облаков.

### Коды из уведомлений

Если вы дадите доступ к уведомлениям, приложение ищет в их тексте одноразовые коды на телефоне. Текст уведомлений не сохраняется; найденный код хранится в памяти 10 минут, первые 3 минуты клавиатура предлагает его первой подсказкой.

### Разрешения

Камера — сканирование паспорта и QR-кодов 2FA. Микрофон — голосовой ввод. NFC — чтение номера, срока и имени владельца банковской карты (имя — если банк записал его на чип; CVV по NFC не передаётся). Уведомления — предложения сохранить пароль. Доступ к уведомлениям (по желанию) — одноразовые коды. Биометрия — разблокировка sPass и подтверждение удаления записей. Фото (по желанию) — скриншоты в буфере клавиатуры. Интернет — функции, перечисленные выше. Каждое разрешение запрашивается только тогда, когда нужна функция.

### Пожертвования

Оплата проходит через Google Play. Данные карты обрабатывает Google; приложение их не получает.

### Обращения в поддержку

Если вы пишете в поддержку или отправляете отчёт об ошибке, письмо отправляет ваше почтовое приложение (например, Gmail) на sboard.app@gmail.com — только после нажатия «Отправить». Мы получаем ваш адрес почты, текст письма и, если вы оставили отметку, версию приложения, версию Android и модель телефона. Эти сведения используются только для ответа и не передаются третьим лицам. Отчёт об ошибке содержит техническое описание сбоя без паролей и данных sPass.

### Третьи лица

Мы не продаём и не передаём ваши данные третьим лицам. Данные попадают к внешним сервисам только в случаях, описанных выше, когда вы пользуетесь соответствующей функцией.

### Удаление данных

Профиль → «Удалить все данные с устройства» стирает хранилище, настройки и выученные слова на телефоне. Удаление приложения тоже удаляет всё локальное. Копии в облаке удаляются в самом облаке (или кнопкой отключения облака в sBoard).

### Дети

Приложение не предназначено специально для детей младше 13 лет и не собирает их данные.

### Изменения и контакты

При существенных изменениях политики приложение попросит подтвердить новую редакцию. Вопросы и запросы: sboard.app@gmail.com (в приложении: Профиль → «Связаться с поддержкой»)

---

## Privacy Policy

_Version of 12 November 2026_

### In short

sBoard is a keyboard and the sPass password manager. The developers run no server of their own: the app creates no account with us, collects no analytics and never sends us what you type. Almost everything works on the phone. All cases where data goes to outside services are listed below — each one is switched on by you.

### What stays on the phone

• Everything you type on the keyboard. Typed text is not stored or sent anywhere.
• Learned words, personal dictionary, quick phrases, clipboard history (text and photos), typing statistics — in the app's storage. Learning is off in password fields. When the keyboard opens it reads the system clipboard to show what was just copied; the content stays on the phone. If you turn on "Screenshots in the clipboard", the keyboard notices new screenshots and copies them into its clipboard; it does not read any other photos.
• sPass entries (passwords, cards, documents, 2FA codes, passkeys) — in a database encrypted with AES-256-GCM under a key derived from the master password (Argon2id). Without the master password, the Recovery Key or a configured recovery method the data cannot be decrypted — by us either.
• Saved personal data for suggestions (phone, e-mail, address) — encrypted on the device and saved only after you confirm.
• Autofill hints before unlocking: the names and logins of your accounts (no passwords or codes) — encrypted with an Android Keystore key, so matching accounts can be shown right away. Turn it off in Profile → Login and recovery.
• Saving from forms: after a login, bank card or personal-data form is sent, Android hands the typed values to sBoard; they stay in memory for at most 5 minutes and go into sPass only after you confirm.
• The keyboard background photo — a copy inside the app.

### Translation

While the translation panel is open, the field text is sent to the service chosen in the translator settings: Google Translate (default) or MyMemory without a key; Google Cloud Translation, Microsoft Translator, DeepL or Yandex Translate with your own API key; LibreTranslate to the server address you entered. If Google Translate or MyMemory is unavailable, the text goes to the other of the two; a service with your own key or server is never replaced by another one. Keys and the address are stored only on the phone and sent only to the chosen service. These companies and server owners process the text under their own terms. Recent translations are kept in memory only and are gone when the app closes. Do not translate confidential text.

Interface language: if the app has no translation for some of its own labels in the chosen language, those labels (never your data or typed text) are translated once through Google Translate and kept on the phone.

### Voice input

Speech is recognised by the Android speech service on your phone (usually from Google). When the device has an offline model, sBoard picks it and audio does not leave the phone; otherwise the service processes audio under its own terms. sBoard does not record or keep audio.

### Other features that use the internet

• GIFs: the search query goes to GIPHY when you open the GIF tab.
• Currency rates for the converter are downloaded once a day from open.er-api.com (no data about you).
• Breach check: only the first 5 characters of the password's SHA-1 hash go to Have I Been Pwned (k-anonymity); the password itself is never sent. The e-mail check sends the address to XposedOrNot — only when you tap the button.
• Site icons: when enabled, the app asks the website of a saved entry for its icon (favicon). The site only sees an icon request.
• Passport scanning (the line of “<” characters) recognises text straight from the camera on the phone (Google ML Kit); frames are not saved or sent, ML Kit may send Google anonymous technical information about how the library works.

### Cloud copies and sign-in

Sync stays off until you connect your own cloud: Google Drive, Dropbox or WebDAV. The copy is encrypted on the phone before upload; the cloud only stores an encrypted file and housekeeping data (size, modification time). Sign-in uses the providers' official mechanisms (Google Sign-In, OAuth 2.0 with PKCE). Access tokens are kept encrypted on the phone. The encrypted copy also holds your settings, learned words and the connection data of your other clouds (the Dropbox token; the WebDAV address, login and app password), so that a new phone connects them by itself. You can disconnect a cloud at any time — local tokens are deleted; sBoard does not revoke access at the provider, so the cloud copy stays. You can remove sBoard's access completely in your provider account settings. For Profile the app shows the picture of your main Google or Dropbox account: its address comes with the account's name and e-mail, and the picture is downloaded once from Google or Dropbox and kept on the phone only. "Delete all data" deletes the sPass copy in every connected cloud and sPass on the phone. When a device is unlinked on another phone, at its next sync it deletes sPass, forgets every cloud sign-in and revokes its Dropbox token at Dropbox.

### Account recovery

The vault opens with the master password or the Recovery Key; neither is ever stored in plain form, on the phone or in the cloud. If you forget both, security questions help: a key derived from the answers (Argon2id) opens the vault only together with a second part, kept on the phone behind its screen lock and in the encrypted copy in your cloud. The answers alone, or a sign-in to the cloud alone, never open the vault. The former "Recovery through the cloud account" mode is gone: after the update its key is removed from the clouds.

### Codes from notifications

If you grant notification access, the app looks for one-time codes in notification text on the phone. Notification text is not stored; a detected code is kept in memory for 10 minutes, and for the first 3 minutes the keyboard offers it as its first suggestion.

### Permissions

Camera — scanning passports and 2FA QR codes. Microphone — voice input. NFC — reading a bank card number, expiry date and holder name (the name only if the bank stored it on the chip; the CVV is never sent over NFC). Notifications — offers to save passwords. Notification access (optional) — one-time codes. Biometrics — unlocking sPass and confirming deletions. Photos (optional) — screenshots in the keyboard clipboard. Internet — the features listed above. Each permission is requested only when its feature is used.

### Donations

Payments go through Google Play. Card data is processed by Google; the app never receives it.

### Contacting support

When you write to support or send an error report, your own mail app (for example Gmail) sends the letter to sboard.app@gmail.com — only after you tap Send. We receive your e-mail address, the text and, if you leave the option on, the app version, Android version and phone model. This is used only to reply and is not shared with third parties. An error report holds a technical description of the failure, without passwords or sPass data.

### Third parties

We do not sell or share your data. Data reaches outside services only in the cases described above, when you use the feature.

### Deleting data

Profile → "Delete all data from this device" erases the vault, settings and learned words on the phone. Uninstalling the app removes everything local as well. Cloud copies are deleted in the cloud itself (or with the disconnect button in sBoard).

### Children

The app is not directed at children under 13 and does not collect their data.

### Changes and contact

If the policy changes in substance, the app will ask you to accept the new version. Questions and requests: sboard.app@gmail.com (in the app: Profile → Contact support)
