# «ТГ-чат-бот «Обучалка английскому языку»

### Основные команды

* /start в первый раз приветствует нового пользователя и добавляет его в БД Далее рандомно достает из БД русское слово и 5 англ с одним верым. Добавляет кнопки и доп кнопки по добавлению, удалению и тренирует дальше.Если слов не достаточно просит добавить новые. 
* Кнопка далее перемешивает слова по новой, ссылаясь на первый пукт.
* Кнопка удаление слов проверят наличие в БД и при подтверждении удаляет Русское и Английкое слово.
* Кнопка добавление слов проверят наличие в БД и при отсутствие добавляет русское слово в БД. Далее через APK translator переводит это слово на англ и добавляет в БД
* /info выводит для пользователя слова, которые он добавил для обучение и их колличество 
* Привильный выбор перевода добавляет слово в список и при 10 привельных ответах и более оповещяют, что слово выучено

*Для БД создано 3 таблицы Пользователи, Русские слова, Английские слова