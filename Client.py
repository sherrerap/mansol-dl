#!/usr/bin/python3
# -*- coding: utf-8 -*-
"usage: {} <url>"

import sys

import Ice
Ice.loadSlice('downloader.ice')
import Downloader
import IceStorm
import binascii

class ProgressEventI(Downloader.ProgressEvent):
    def notify(self, clipData, current=None):
        print("[INFO] Estado de la descarga:", clipData.status)

class Client(Ice.Application):
    
    def menu(self):
        print('\033[1m')
        print("Seleccione una opción:")
        print("1-Descargar una canción")
        print("2-Mostrar las canciones del servidor")
        print("3-Copiar una canción del servidor")
        print("4-Salir")
        print('\033[0m')
        opcion = input()
        return opcion

    def get_topic_manager(self):
        key = 'IceStorm.TopicManager.Proxy'
        proxy = self.communicator().propertyToProxy(key)
        if proxy is None:
            print ("property", key, "not set")
            return None

        print("Using IceStorm in: '%s'" % key)
        return IceStorm.TopicManagerPrx.checkedCast(proxy)
    
    def receive(self,transfer, destination_file):
        BLOCK_SIZE = 10240
        '''
        Read a complete file using a Downloader.Transfer object
        '''
        with open(destination_file, 'wb') as file_contents:
            remoteEOF = False
            while not remoteEOF:
                data = transfer.recv(BLOCK_SIZE)
                # Remove additional byte added by str() at server
                if len(data) > 1:
                    data = data[1:]
                data = binascii.a2b_base64(data)
                remoteEOF = len(data) < BLOCK_SIZE
                if data:
                    file_contents.write(data)
            transfer.end()


    def run(self, argv):
        contador = 0
        topic_mgr = self.get_topic_manager()
        if not topic_mgr:
            print (': invalid proxy')
            return 2

        ic = self.communicator()
        servant = ProgressEventI()
        adapter = ic.createObjectAdapter("ProgressAdapter")
        subscriber = adapter.addWithUUID(servant)

        topic_name = "ProgressTopic"
        qos = {}
        try:
            topic = topic_mgr.retrieve(topic_name)
        except IceStorm.NoSuchTopic:
            topic = topic_mgr.create(topic_name)

        topic.subscribeAndGetPublisher(qos, subscriber)

        base = self.communicator().stringToProxy(argv[1])
        sf = Downloader.SchedulerFactoryPrx.checkedCast(base)

        if not sf:
            raise RuntimeError("Invalid proxy")
        
        while(True):
            opcion = self.menu()

            if(opcion == '1'):
                contador = contador + 1
                print("[INFO] Especifique la dirección url del vídeo: ")
                url = input()
                nombre = 'Servidor ' + str(contador)
                adapter.activate()
                dl = sf.make(nombre)
                dl.addDownloadTask(url)
                topic.unsubscribe(subscriber)
                print()
                print('\033[36m' + "[INFO] Descarga completada correctamente, puedes encontrar tu canción en el servidor." + '\033[0m')
                print()
                sf.kill(nombre)
                
            elif(opcion == '2'):
                contador = contador + 1
                print("[INFO] Canciones disponibles en el servidor: ")
                nombre = 'Servidor ' + str(contador)
                dl = sf.make(nombre)
                songs = dl.getSongList()
                for i in songs:
                    print('[♫ ]', i)
                sf.kill(nombre)
                    
            elif(opcion == '3'):
                contador = contador + 1
                print('[INFO] Indique el nombre específico de la canción.')
                print('[INFO] Asegúrese de poner el mismo nombre que el que aparece en la lista de canciones:')
                cancion = input()
                
                nombre = 'Servidor ' + str(contador)
                dl = sf.make(nombre)
                
                try:
                    transfer = dl.get(cancion)
                    self.receive(transfer,cancion)
                    print()
                    print('\033[36m' + "[INFO] " + cancion + " recibida correctamente." + '\033[0m')
                    print()
                except Exception as e:
                    print("[ERROR] Esa canción no está disponible en el servidor.")
                
            elif(opcion == '4'):
                return 0;
                
            else:
                print("[INFO] Selecciona una opcion válida:")

        
        return 0


if len(sys.argv) != 3:
    print(__doc__.format(__file__))
    sys.exit(1)


app = Client()
sys.exit(app.main(sys.argv))
