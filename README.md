# Server - SIRTApp
Server side application for SIRT application - el *backend* para SIRTApp

[![Build Status](https://travis-ci.com/SIRTDetection/Server.svg?branch=master)](https://travis-ci.com/SIRTDetection/Server)
![License](https://img.shields.io/github/license/SIRTDetection/Server.svg?style=flat-square)
![Python version](https://img.shields.io/badge/python-%3E%3D3.6-green.svg?style=flat-square&logo=python)

## Índice

1. [Introdución](#1-introducción)
2. [Retos](#2-retos)
3. [Dependencias](#3-dependencias)
4. [Desarrollo](#4-desarrollo)
5. [Instalación](#5-instalación)
6. [Licencia](#6-licencia)

------------------------

### 1. Introducción

Cuando se propuso el trabajo en grupo, viendo lo que habíamos estudiado en la asignatura (*OpenCV*, 
algoritmos evolutivos, etc.) pensamos inmediatamente en hacer un sistema que, aprovechando todos
esos recursos, pudiera detectar **en tiempo real** los objetos que aparecían en una imagen. Es decir,
el usuario estaría emitiendo continuamente fotogramas que serían procesados por un *backend* (el servidor,
en este caso).

A raíz de ese planteamiento inicial, se nos ocurrió también que se podría dar la opción al usuario para
que pudiera **corregir la predicción** de la aplicación: si detecta erróneamente un **vaso** cuando, en realidad,
es un *estuche*, el usuario **podría seleccionar la sección correspondiente al objeto en cuestión** e
incluir el valor que él quisiera, para que en una **situación similar** el servidor tuviera en cuenta
la consideración del mismo.

Con dichas ideas en mente, nos pusimos a buscar *dataset* que contuvieran, al menos, varios GB de 
imágenes, ya que pretendíamos que el modelo fuera capaz de identificar casi cualquier objeto. Tras varios
días de búsqueda, nos decantamos por el *[Open Images Dataset V4](https://storage.googleapis.com/openimages/web/download.html)*,
el cual contiene cerca de **50 TB** en imágenes, con las cuales tendríamos información suficiente para poder clasificar
casi cualquier objeto.

### 2. Retos

Teniendo en cuenta las consideraciones anteriores, nos enfrentamos a los siguientes retos (también se
incluyen las determinaciones finales sobre los mismos):

- La **cantidad de imágenes** iniciales (~50 TB) nos pareció interesante, ya que abría muchas posibilidades.
  Pero debido a la no disposición de *almacenamiento suficiente* y, sobre todo, a la falta de potencia de cálculo,
  desistimos al intentar esta opción: todos los *entrenamientos* habían sido realizados con tarjetas gráficas
  [NVIDIA Tesla P100](https://www.nvidia.com/en-us/data-center/tesla-p100/), en donde para solo **27 GB** de datos
  (recordemos que nosotros disponíamos de varios terabytes) habían dedicado *9 horas de computación*, y para un *dataset*
  de ~75 GB, **27 horas de cómputo**.
  
  Ante esta problemática, nos pusimos a buscar soluciones las cuales no precisaran de una gran capacidad
  de cómputo por nuestra parte, sino aprovechar **aquellos dataset** ya procesados por otros: empezamos a usar 
  *[Tensorflow](https://www.tensorflow.org)*. Investigando, descubrimos que ya habían empezado a desarrollar
  un sistema de *detección de objetos* (*[Object detection API](https://github.com/tensorflow/models/tree/master/research/object_detection)*)
  que cumplía perfectamente con nuestras necesidades y espectativas: disponía de una amplia variedad de **clases**
  de objetos los cuales podía detectar así como de *varios modelos [ya entrenados](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md#coco-trained-models)*
  los cuales varían entre sí en lo que se refiere a **velocidad** y **precisión**, por lo cual se convirtió en
  nuestra decisión definitiva.
  
- El procesamiento **en tiempo real** nos pareció una idea muy interesante para intentar obtener un resultado
  muy agradable y evidente de la *detección de objetos*, pero al igual que nos ocurría en el apartado anterior, 
  teníamos un problema de **capacidad de cálculo**. 
  
  Al principio, probamos con *modelos pre-entrenados* con una **buena precisión** y un tiempo de cómputo *aceptable*
  (~70 ms.), pero dichos tiempos equivalían a la detección con el *hardware* mencionado anteriormente, y en el equipo
  de procesado se extendía a **30 - 40 segundos**. Finalmente, usamos un modelo conocido como
  *[MobileNet V2 Coco](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md#coco-trained-models)*
  el cual ofrecía buenos tiempos (~26 ms.) y que en nuestros dispositivos se extendía a **~1'5 segundos**.
  
  Dicho tiempo es *aceptable* para el procesado de una única imagen, pero inservible para *una transmisión media de 30 
  fotogramas por segundo*, por lo que finalmente decidimos únicamente detectar **imágenes** enviadas individualmente.
  
- El añadido de que **el usuario pudiera predefinir** sus propios modelos implicaba:
  
  - Cada usuario tendría que *disponer de un modelo* único, para que así los cambios que cada uno
    realizara sobre su modelo no **afectaran a los demás**.
  - Programar y crear la **lógica de detección** de los modelos, para asegurarse de que el sistema
    basado en *labels* y *boxes* (etiquetas y cuadrados) funcionara correctamente.
  - El modelo se tiene que **volver a entrenar** por cada nuevo elemento creado por el usuario. Esto
    implicaba toda aquella *potencia de cómputo* que mencionamos en el primer caso la cual nos
    impidió usar nuestro propio modelo.
  
  Por todos estos problemas, además de la propia complejidad que implicaba **desarrollar un nuevo
  entrenamiento** sobre un *modelo ya entrenado*, descartamos esta opción. Para futuras versiones se 
  podría plantear como un posible añadido.
  
- La comunicación entre *lenguajes de programación* fue también un factor decisivo, ya que necesitábamos
  que el *backend* (escrito en **Python**) tuviera la capacidad total de comunicación con el *frontend*
  (desarrollado en **Java**). Para solventar esta parte, decidimos desarrollar un **servidor web** 
  que escuche a las distintas peticiones que reciba mediente un API REST.
  
### 3. Dependencias

+ **Flask**: *[flask](http://flask.pocoo.org/)* es un *framework* que permite crear un *webhook*
  que atienda a las distintas peticiones, recibir archivos y generar respuestas, en forma de archivos
  binarios o bien tipo **JSON**.

+ **Tensorflow**: *[Tensorflow](https://www.tensorflow.org)* es uno de los *framework* *Open Source*
  más famosos hoy en día. Gracias al impulso de Google, se ha convertido en la opción preferida de muchos
  en el campo de la inteligencia artificial por su simpleza y, sobre todo, su potencia.

+ **Pandas**: *[Pandas](https://pandas.pydata.org/)* es una librería de análisis de datos para Python.
  Existe casi desde el comienzo de este lenguaje de programación, pero sus últimos desarrollos y mejoras
  han hecho que gane en fuerza por las amplias posibilidades que ofrece.

+ **Keras**: *[Keras](https://keras.io/)* es la librería principal en la que se apoya *Tensorflow*.
  Concebida como una librería de **deep learning**, Keras es actualmente la opción más usada para
  implementar algoritmos de inteligencia artificial.

+ **Numpy**: *[numpy](http://www.numpy.org/)* es la solución ideal para el cálculo matricial en **Python**.
  Con capacidad de hasta *N-dimensiones*, numpy se convierte actualmente en la opción ideal para el
  procesamiento de imágenes (píxeles) y el trabajo con matrices en el campo de la inteligencia artificial.
  
+ Y **más**: al final existen muchas dependencias con otros paquetes que han desarrollado profesionales
  del sector, que ayudan a un desarrollo más rápido de aplicaciones nuevas. Todas las librerías usadas
  están disponibles en el archivo *[requirements.txt](https://github.com/SIRTDetection/Server/blob/master/server/requirements.txt)*
  de este mismo proyecto.
  
### 4. Desarrollo

La aplicación que hoy se ejecuta en el servidor tuvo varios procesos de desarrollo:

#### 4.1. El servidor web

La primera lógica desarrollada fue la parte **web** de la aplicación. Esto es debido a que, hasta
que no estuviera completamente estructurada, no sería posible el inicio del desarrollo de la 
aplicación Android, que a fin de cuentas es la parte visible de lo que se ejecuta en el *backend*.

El servidor web consta de un *webhook* desarrollado en **flask** el cual se basa en la API REST.
El usuario solicitará un *token* al servidor, usando para ello su **UUID** y el servidor registrará 
y conservará los datos pertenecientes al mismo en un *diccionario*:

```python
uuid = { 'token': "token_del_usuario",
         'first_connection': 'datetime_con_la_primera_conexión',
         'latest_connection': 'datetime_con_la_última_conexión'
}
``` 

Dicho diccionario se comprobará cada vez para ver que el *token* no haya cambiado así como, a nivel
estadístico, registrar las conexiones del usuario.

Una vez el usuario ya tenía su *token*, podía empezar inmediatamente a enviar imágenes para así
procesarlas y obtener los resultados. Para ello, se hacía una petición **POST** en donde se añadía,
en el campo *`"picture"`* de archivos la imagen a procesar. El servidor gestionaba la petición y
o bien devolvía la imagen procesada o bien un error con su explicación, el cual habría de ser gestionado
en la aplicación Android.

#### 4.2. Tensorflow

Aunque la API de detección de objetos *ya estuviera desarrollada*, aquí una parte fundamental era
la comunicación entre la **imagen** que enviaba el usuario y la **imagen** que tenía que gestionar
el servidor.

Para ello, se creó una clase completa la cual *obtiene, normaliza y deja* las imágenes aptas
para ser procesadas por la librería, y así evitar posibles errores por incompatibilidad. Así, la clase
`tensorflow_worker` crearía una única `Session()` para agilizar el procesado y cambiaría el tamaño
de la imagen, aplicaría factores de corrección y finalmente identificaría aquellos objetos presentes
en la misma para así poder generar un `stream` de `bytes` con el resultado de la inferencia gráfica.

### 5. Instalación

Para una agilización del proceso y de las actualizaciones, se creó un *script* `start_server.sh`, 
el cual se encarga de la **gestión de dependencias** y actualizaciones de los paquetes.

*Tensorflow* usa librerías del tipo *proto*, las cuales necesitan una compilación la primera vez que
se van a utilizar. Además, necesita de varias dependencias *ajenas a Python* las cuales se han de instalar
con un gestor de paquetes. Como el servidor que hemos usado utiliza un sistema tipo **Debian**, el *script*
está desarrollado en `bash`.

Para instalar el servidor, se puede:
```bash
wget https://raw.githubusercontent.com/SIRTDetection/Server/master/server/start_server.sh
```

Se obtiene el archivo y se establecen permisos de ejecución:
```bash
chmod +x start_server.sh
sudo ./start_server.sh
```

De esta manera, se instalará y ejecutará el servidor la primera vez. Para las siguientes, 
hay que meterse en la carpeta: `Server/server` y ejecutar el mismo archivo.

### 6. Licencia

    Copyright (C) 2018 - present  SIRTDetection

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
