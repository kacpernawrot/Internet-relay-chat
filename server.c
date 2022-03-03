#include <netdb.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <pthread.h>
#include <time.h>

#define MAX_USR 10
#define QUEUE_SIZE 255

struct User
{
    int cfd;
    char channel[200];
    char name[20];
    struct sockaddr_in caddr;
};

struct User Users[MAX_USR] = {0};



//Function that checks if there is a place for a new user. If so, it creates temporary user.
int create_temporary_user(struct User *user)
{
    for (int i = 0; i < MAX_USR; i++)
    {
        if (Users[i].cfd == 0)
        {
            Users[i].cfd = (*user).cfd;
            Users[i].caddr = (*user).caddr;
            return 1;
        }
    }

    return 0;
};

//Function that checks if the username is available.
int nick_taken(char *nick)
{
    for (int i = 0; i < MAX_USR; i++)
    {
        if (strcmp(Users[i].name, nick) == 0)
        {
            return 0;
        }
    }

    return 1;
};

//Function that returns user's index from Users array.
int user_index(int cfd)
{

    for (int i = 0; i < MAX_USR; i++)
    {
        if (Users[i].cfd == cfd)
        {
            return i;
        }
    }

    return -1;
};

//Function that replaces temporary user with an actual user.
int create_user(int cfd, char *nick)
{
    int index = user_index(cfd);

    if (nick_taken(nick))
    {
        strcpy(Users[index].name, nick);
        return 1;
    }

    return 0;
};

//Function that deletes user from server (disconnect).
int delete_user(int cfd)
{
    int index = user_index(cfd);

    if (index >= 0)
    {
        memset(&Users[index], 0, sizeof(struct User));
        return 1;
    }

    return 0;
};

//Function that allocates user to a channel.
int connect_to_channel(int cfd, char channel[])
{
    int index = user_index(cfd);

    if (index >= 0)
    {
        strcpy(Users[index].channel, channel);
        return 1;
    }

    return 0;
}




//Function that sends information to all users.
void Broadcast(char channel[], char message[])
{

    for (int i = 0; i < MAX_USR; i++)
    {
        if (strncmp(Users[i].channel, channel, strlen(channel)) == 0)
        {
            write(Users[i].cfd, message, strlen(message));
        }
    }
}


//Function that handles client's requests.
void *client_service(void *arg)
{
    char message[255] = {0};
    struct User *c = (struct User *)arg;

    int rc = read((*c).cfd, message, 255);
    int userAdded = create_temporary_user(c);

    if (userAdded == 0)
    {
        write((*c).cfd, "Maximum users reached.\n", 24);
        close((*c).cfd);
        free(c);
        return EXIT_SUCCESS;
    }

    while (rc > 0)
    {
        int userIndex = user_index((*c).cfd);
        struct User *user;
        if (userIndex >= 0)
        {
            user = &Users[userIndex];
        }

        //commands handling
        //                                          /nick - sets username, /exit - disconnects from server -> for server only
        // /h - help, /c - change channel or create private channel, /u - display users on current channel -> for client only
        if (strncmp(message, "/", 1) == 0)
        {
            char *command = strtok(message, " ");
            char *argument = strtok(NULL, " ");
            //Set username and connect user to server
            if (strncmp(command, "/nick", 5) == 0)
            {
                char tempName[255] = {0};
                int length = sizeof((*user).name);
                strncpy(tempName, (*user).name, length);


                if (strcmp((*user).name, "") == 0)
                {
                    if (create_user((*c).cfd, argument) == 1)
                    {
                        write((*c).cfd, "connected", 9);
                        memset(message, 0, sizeof(message));
                    }

                    else
                    {
                        write((*c).cfd, "User cannot be created\n", 24);
                        memset(message, 0, sizeof(message));
                    }
                }
            }
            //Disconnect and remove user
            else if (strncmp(command, "/exit", 6) == 0)
            {
                char tempName[20] = {0};
                strncpy(tempName, (*user).name, sizeof((*user).name));
                char tempChannel[200] = {0};
                strncpy(tempChannel, (*user).channel, sizeof((*user).channel));

                if (delete_user((*c).cfd) == 1)
                {
                    char toSend[255] = {0};
                    snprintf(toSend, sizeof(toSend), "User %s has disconnected from server.", tempName);
                    //Display that user has disconnected only to users who shared channel with them.
                    for(int d = 0; d < MAX_USR; d++)
                    {
                        if(strcmp(Users[d].channel, tempChannel) == 0)
                        {
                            write(Users[d].cfd, toSend, strlen(toSend));
                        }
                    }
                    memset(message, 0, sizeof(message));

                    rc = 0;
                }

                else
                {
                    puts("Error while disconnecting client!");
                    close((*c).cfd);
                }
            }
            //Display available commands.
            else if (strncmp(command, "/h", 2) == 0)
            {
                char toSend[255] = {0};

                snprintf(toSend, sizeof(toSend), "\n/c [name of channel] - connect to the given channel.");
                write((*c).cfd, toSend, strlen(toSend));
                memset(toSend, 0, sizeof(toSend));

                snprintf(toSend, sizeof(toSend), "\nIf given channel currently doesn't exist, chat will create one.\n");
                write((*c).cfd, toSend, strlen(toSend));
                memset(toSend, 0, sizeof(toSend));

                snprintf(toSend, sizeof(toSend), "\n/u - prints the list of users connected to this channel.\n");
                write((*c).cfd, toSend, strlen(toSend));
                memset(toSend, 0, sizeof(toSend));

                snprintf(toSend, sizeof(toSend), "\n/h - prints help.\n");
                write((*c).cfd, toSend, strlen(toSend));
                memset(toSend, 0, sizeof(toSend));
            }
            //Display available users on current channel.
            else if (strncmp(command, "/u", 2) == 0)
            {
                char toSend[255] = {0};
                snprintf(toSend, sizeof(toSend), "\nList of users in this channel:\n");
                write((*c).cfd, toSend, strlen(toSend));
                memset(toSend, 0, sizeof(toSend));

                for(int i = 0; i < MAX_USR; i++)
                {
                    if(strcmp((*user).channel, Users[i].channel) == 0)
                    {
                        snprintf(toSend, sizeof(toSend), "%s\n", Users[i].name);
                        write((*c).cfd, toSend, strlen(toSend));
                        memset(toSend, 0, sizeof(toSend));
                    }
                }
            }
            //Change channel or create one if it doesn't exist.
            else if (strncmp(command, "/c", 2) == 0)
            {
                char tempChannel[200] = {0};
                strncpy(tempChannel, (*user).channel, sizeof((*user).channel));

				//setting user channel during first connection
                if (strcmp((*user).channel, "") == 0)
                {
                    if (connect_to_channel((*c).cfd, argument) == 1)
                    {
                        char toSendNew[255] = {0};
                        snprintf(toSendNew, sizeof(toSendNew), "User %s has joined channel %s.", Users[userIndex].name, Users[userIndex].channel);
						//Display user that joined a channel.
                        Broadcast(Users[userIndex].channel, toSendNew);
                        memset(message, 0, sizeof(message));
                    }

                    else
                    {
                        write((*c).cfd, "Cannot set users channel\n", 26);
                        memset(message, 0, sizeof(message));
                    }
                }
                //Display states about user when swapping channels.
                else
                {
                    if (connect_to_channel((*c).cfd, argument) == 1)
                    {

                        char toSendOld[255] = {0};
                        char toSendNew[255] = {0};
                        snprintf(toSendNew, sizeof(toSendNew), "User %s has joined channel %s.", Users[userIndex].name, Users[userIndex].channel);
                        snprintf(toSendOld, sizeof(toSendOld), "User %s has left channel %s.", Users[userIndex].name, tempChannel);
                        Broadcast(tempChannel, toSendOld);
                        Broadcast(Users[userIndex].channel, toSendNew);
                        memset(message, 0, sizeof(message));
                    }

                    else
                    {
                        write((*c).cfd, "Cannot set users channel\n", 26);
                        memset(message, 0, sizeof(message));
                    }
                }
            }

            else
            {
                write((*c).cfd, "Incorrect command.", 20);
            }
            rc = read((*c).cfd, message, 255);
        }
        //Display given messages by user.
        else
        {
            if ((*user).name && (*user).channel)
            {
                time_t now = time(NULL);
                struct tm tm_now ;
                localtime_r(&now, &tm_now);
                char buff[100];
                strftime(buff, sizeof(buff), "%H:%M:%S", &tm_now);
                char toSend[255] = {0};
                strcat(toSend, buff);
                strcat(toSend," [");
                strcat(toSend, (*user).name);
                strcat(toSend, "]: ");
                strcat(toSend, message);
                Broadcast((*user).channel, toSend);
                memset(message, 0, sizeof(message));
            }

            else
            {
                write((*c).cfd, "Invalid nick or channel!\n", 30);
                memset(message, 0, sizeof(message));
            }
            rc = read((*c).cfd, message, 255);
        }
    }

    close((*c).cfd);
    free(c);
    return EXIT_SUCCESS;
}

int main(int argc, char **argv)
{
    pthread_t tid;
    socklen_t slt;
    int sfd, on = 1;
    struct sockaddr_in saddr;

    for (int i = 0; i < MAX_USR; i++)
    {
        delete_user(Users[i].cfd);
    }

    sfd = socket(AF_INET, SOCK_STREAM, 0);

    if (sfd < 0) {
        printf("Error trying to create a socket!\n");
        exit(1);
    }

    saddr.sin_family = AF_INET;
    saddr.sin_addr.s_addr = INADDR_ANY;
    saddr.sin_port = htons(1234);
    setsockopt(sfd, SOL_SOCKET, SO_REUSEADDR, (char *)&on, sizeof(on));

    if (bind(sfd, (struct sockaddr *)&saddr, sizeof(saddr)) < 0) {
        printf("Error trying to bind an IP address and port number to the socket!\n");
        exit(1);
    }

    if (listen(sfd, QUEUE_SIZE) < 0) {
        printf("Error trying to set the queue size!\n");
        exit(1);
    }

    while (1)
    {
        struct User *c = malloc(sizeof(struct User));
        slt = sizeof((*c).caddr);
        (*c).cfd = accept(sfd, (struct sockaddr *)&(*c).caddr, &slt);
        printf("CFD: %d\n", (*c).cfd);
        pthread_create(&tid, NULL, client_service, c);
        pthread_detach(tid);
    }
    close(sfd);
    return EXIT_SUCCESS;
}


