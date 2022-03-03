# Komunikator internetowy typu IRC– sprawozdanie z projektu SK2
Michał Olszewski 144482
Kacper Nawrot 145246


1. Opis protokołu komunikacyjnego.

    ## Serwer: 
    Serwer inicjowany jest o adresie IP komputera oraz numerze portu 1234. Serwer posiada z góry maksymalną liczbę użytkowników mogących zalogować się do czatu. Serwer najpierw próbuje nawiązać połączenie z użytkownikiem, jeżeli próba się powiedzie tworzy nowy wątek, na którym serwer nasłuchuje wiadomości klienta. Po otrzymaniu wiadomości serwer klasyfikuje otrzymaną wiadomość jako komendę lub zwykłą wiadomość. Jeżeli serwer otrzymał zwykłą wiadomość, wypisuje ją na chacie użytkowników podłączonych do danego kanału. Komendy poprzedzane są znakiem `/`. 

    `/nick` „nazwa_uzytkownika” – przypisanie nazwy użytkownika.<br />
    `/exit` – rozłączenie się z serwerem.<br />
    `/c nazwa_kanału` – stworzenie kanału prywatnego, bądź dołączenie do już istniejącego kanału o podanej nazwie.<br />
    `/u` – wypisanie użytkowników podłączonych do kanału w którym użytkownik obecnie się znajduje.<br />
    `/h` – wypisanie wszystkich dostępnych komend, wraz z opisem ich akcji.<br />
    

    ## Klient:
    Po wypełnieniu formularza logowania, wysyłana jest na serwer komenda /nick „nazwa_użytkownika” która ustawia nazwę użytkownika. Następnie użytkownik z panelu czatu musi wybrać jeden z 3 dostępnych pokojów (Alpha, Beta, Delta) lub za pomocą polecenia /c „nazwa_kanału”  połączyć się do kanału. Po dołączeniu do kanału do wszystkich zalogowanych użytkowników w tym kanale wysyłany jest komunikat o zalogowaniu się przez nowego użytkownika, w identyczny sposób przekazywany jest komunikat o zmienieniu kanału lub rozłączeniu się z czatu. 

2. Opis zawartości plików źródłowych oraz sposób kompilacji i uruchomienia.

    • `server.c` – plik zawierający kod źródłowy serwera.

    • `client.py` – plik zawierający kod źródłowy klienta wraz z jego graficznym interfejsem.
    
    
Kompilacja serwera: `gcc ./server.c -o server -pthread – Wall` 

Uruchomienie serwera: `./server`

Uruchomienie klienta:`python3 client.py`
