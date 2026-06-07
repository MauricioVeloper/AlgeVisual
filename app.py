from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect, url_for
from Modelo import tarea
from Modelo.entrega import Entrega
from Modelo.tarea import Tarea
from database import SessionLocal
from Modelo.usuario import Usuario
from Modelo.estudiante import Estudiante
from Modelo.estudiante import Estudiante
from Modelo.docente import Docente
from Modelo.grupo import Grupo
from Modelo.grupo_estudiante import GrupoEstudiante
from Modelo.mensaje import Mensaje
from sqlalchemy import or_, and_
from sqlalchemy import text
from sqlalchemy.orm import joinedload
import uuid
from Modelo.comentario_tarea import ComentarioTarea
from Modelo.calificacion import Calificacion
from flask import jsonify 
from Modelo.actividad import Actividad, PreguntaExamen, OpcionPregunta
from datetime import datetime 

app = Flask(__name__, template_folder='Vista')
# Clave secreta necesaria para encriptar las cookies de sesión de los usuarios
app.secret_key = 'algevisual_clave_super_secreta' 

# Configuración para guardar imágenes de perfil
app.config['UPLOAD_FOLDER'] = 'static/uploads/perfiles'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# Configuración para guardar archivos de tareas
app.config['UPLOAD_FOLDER_TAREAS'] = 'static/uploads/tareas'
os.makedirs(app.config['UPLOAD_FOLDER_TAREAS'], exist_ok=True)
# Carpeta para las entregas de los alumnos
app.config['UPLOAD_FOLDER_ENTREGAS'] = 'static/uploads/entregas'
os.makedirs(app.config['UPLOAD_FOLDER_ENTREGAS'], exist_ok=True)

@app.route('/')
def inicio():
    # Si ya hay una sesión activa, lo mandamos directo al panel
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    correo_ingresado = request.form.get('correo')
    contrasena_ingresada = request.form.get('contrasena')

    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(
        Correo=correo_ingresado, 
        Contrasena=contrasena_ingresada, 
        Estado=True
    ).first()
    db.close()

    if usuario:
        # Guardamos los datos importantes en la sesión
        session['usuario_id'] = usuario.ID_Usuario
        session['nombre'] = usuario.NombreCompleto
        session['rol'] = usuario.Rol
        session['foto'] = usuario.FotoPerfil
        # Lo redirigimos a la nueva ruta del panel de control
        return redirect(url_for('dashboard'))
    else:
        return f"<h1 style='color: red; text-align: center;'>Error: Correo o contraseña incorrectos.</h1><br><a href='/'>Volver a intentar</a>"

# NUEVA RUTA: El Panel de Control
# RUTA: Menú Principal (Adaptado por Roles)
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    db = SessionLocal()
    rol = session.get('rol')
    usuario_id = session.get('usuario_id')
    
    mis_grupos = []
    
    # LÓGICA SEGÚN EL ROL DEL USUARIO
    if rol == 'Estudiante':
        # Busca los grupos a los que se unió
        mis_inscripciones = db.query(GrupoEstudiante).filter_by(ID_Estudiante=usuario_id).all()
        mis_grupos = [insc.grupo for insc in mis_inscripciones if insc.grupo.Estado == True]
        
    elif rol == 'Docente':
        # Busca exclusivamente los grupos que él ha creado/imparte
        mis_grupos = db.query(Grupo).filter_by(ID_Docente=usuario_id, Estado=True).all()
        
    elif rol == 'Administrador':
        # El administrador puede ver todos los grupos activos
        mis_grupos = db.query(Grupo).filter_by(Estado=True).all()
        
    db.close()
    
    return render_template('dashboard.html', nombre=session['nombre'], rol=rol, mis_grupos=mis_grupos)
@app.route('/logout')
def logout():
    session.clear() # Borramos la memoria
    return redirect(url_for('inicio'))

@app.route('/estudiantes')
def estudiantes():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    # Capturamos el parámetro de búsqueda si es que el usuario usó el filtro
    criterio = request.args.get('buscar', '')

    db = SessionLocal()
    # -----------------------------------------------------  RF_03  -----------------------------------------------------
    # Consulta base: traemos solo usuarios cuyo rol sea Estudiante y estén activos (Estado=True)
    query = db.query(Estudiante).join(Usuario)
    
    if criterio:
        # Aplicamos el filtro de búsqueda (RF_03) por Nombre o Matrícula
        query = query.filter(
            (Usuario.NombreCompleto.like(f"%{criterio}%")) | 
            (Usuario.Matricula.like(f"%{criterio}%"))
        )
    
    lista_alumnos = query.filter(Usuario.Estado == True).all()
    db.close()
    
    return render_template('estudiantes.html', alumnos=lista_alumnos)
# -----------------------------------------------------  RF_01  -----------------------------------------------------
@app.route('/estudiantes/registrar', methods=['GET', 'POST'])
def registrar_estudiante():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        matricula = request.form.get('matricula')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        
        db = SessionLocal()
        
        # Validación interna de duplicados (Evitamos fallos críticos de llaves únicas)
        existe = db.query(Usuario).filter((Usuario.Matricula == matricula) | (Usuario.Correo == correo)).first()
        if existe:
            db.close()
            return f"<h1 style='color: red; text-align: center;'>Error: La matrícula o el correo ya se encuentran registrados.</h1><br><a href='/estudiantes/registrar'>Volver al formulario</a>"
        
        try:
            # 1. Crear el registro base en Usuarios
            nuevo_usuario = Usuario(
                Matricula=matricula,
                NombreCompleto=nombre,
                Correo=correo,
                Contrasena=contrasena,
                Rol='Estudiante',
                Estado=True
            )
            db.add(nuevo_usuario)
            db.flush() # Envía el cambio y recupera el ID autogenerado sin cerrar la transacción
            
            # 2. Crear el registro en la tabla hija enlazando el ID_Usuario
            nuevo_estudiante = Estudiante(ID_Estudiante=nuevo_usuario.ID_Usuario)
            db.add(nuevo_estudiante)
            
            db.commit() # Consolidamos ambas inserciones en SQL Server
        except Exception as e:
            db.rollback()
            return f"Hubo un error al procesar el alta: {str(e)}"
        finally:
            db.close()
            
        return redirect(url_for('estudiantes'))
        
    return render_template('registrar_estudiante.html')

# -----------------------------------------------------  RF_05  -----------------------------------------------------
@app.route('/estudiantes/baja/<int:id_alumno>')
def baja_estudiante(id_alumno):
    # Verificamos seguridad
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    db = SessionLocal()
    
    # Buscamos al usuario por su ID
    usuario_a_baja = db.query(Usuario).filter_by(ID_Usuario=id_alumno).first()
    
    if usuario_a_baja:
        # En lugar de eliminarlo (DELETE), hacemos la baja lógica (UPDATE Estado = False)
        usuario_a_baja.Estado = False
        db.commit()
        
    db.close()
    
    # Recargamos la tabla de alumnos
    return redirect(url_for('estudiantes'))


# -----------------------------------------------------  RF_04  -----------------------------------------------------
@app.route('/estudiantes/modificar/<int:id_alumno>', methods=['GET', 'POST'])
def modificar_estudiante(id_alumno):
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    alumno_a_modificar = db.query(Usuario).filter_by(ID_Usuario=id_alumno).first()
    
    # Si el usuario presiona "Guardar Cambios"
    if request.method == 'POST':
        alumno_a_modificar.NombreCompleto = request.form.get('nombre')
        alumno_a_modificar.Matricula = request.form.get('matricula')
        alumno_a_modificar.Correo = request.form.get('correo')
        
        # Solo actualizamos la contraseña si el administrador escribió algo en la caja
        nueva_contrasena = request.form.get('contrasena')
        if nueva_contrasena:
            alumno_a_modificar.Contrasena = nueva_contrasena
            
        db.commit()
        db.close()
        return redirect(url_for('estudiantes'))
        
    db.close()
    # Si solo está entrando a ver la pantalla, le mandamos los datos actuales
    return render_template('modificar_estudiante.html', alumno=alumno_a_modificar)

# -----------------------------------------------------  RF_07  -----------------------------------------------------
    # RUTA 1: Mostrar la lista de docentes
@app.route('/docentes')
def docentes():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    criterio = request.args.get('buscar', '')
    db = SessionLocal()
    
    query = db.query(Docente).join(Usuario)
    
    if criterio:
        query = query.filter(
            (Usuario.NombreCompleto.like(f"%{criterio}%")) | 
            (Usuario.Matricula.like(f"%{criterio}%"))
        )
    
    lista_docentes = query.filter(Usuario.Estado == True).all()
    db.close()
    
    return render_template('docentes.html', docentes=lista_docentes)

# -----------------------------------------------------  RF_06  -----------------------------------------------------
# RUTA 2: Procesar el registro del docente
@app.route('/docentes/registrar', methods=['POST'])
def registrar_docente():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    # Atrapamos los campos separados
    nombres = request.form.get('nombres')
    apellido_paterno = request.form.get('apellido_paterno')
    apellido_materno = request.form.get('apellido_materno', '')
    
    # Los unimos para el sistema general
    nombre_completo = f"{nombres} {apellido_paterno} {apellido_materno}".strip()
    
    matricula = request.form.get('matricula')
    correo = request.form.get('correo')
    contrasena = request.form.get('contrasena')
    descripcion = request.form.get('descripcion')
    
    db = SessionLocal()
    
    existe = db.query(Usuario).filter((Usuario.Matricula == matricula) | (Usuario.Correo == correo)).first()
    if existe:
        db.close()
        return f"<h1 style='color: red; text-align: center;'>Error: El número de empleado o correo ya existe.</h1><br><a href='/docentes'>Volver</a>"
    
    try:
        # Guardamos tanto el nombre completo como los fragmentos separados
        nuevo_usuario = Usuario(
            Matricula=matricula, NombreCompleto=nombre_completo, 
            Nombres=nombres, ApellidoPaterno=apellido_paterno, ApellidoMaterno=apellido_materno,
            Correo=correo, Contrasena=contrasena, Rol='Docente', Estado=True
        )
        db.add(nuevo_usuario)
        db.flush() 
        
        # 2. Crear registro en la tabla hija Docentes
        nuevo_docente = Docente(ID_Docente=nuevo_usuario.ID_Usuario, Descripcion=descripcion)
        db.add(nuevo_docente)
        
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Error al guardar: {str(e)}"
    finally:
        db.close()
        
    return redirect(url_for('docentes'))

# -----------------------------------------------------  RF_08  -----------------------------------------------------
    # RUTA: Dar de baja a un docente
@app.route('/docentes/baja/<int:id_docente>')
def baja_docente(id_docente):
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    db = SessionLocal()
    usuario_a_baja = db.query(Usuario).filter_by(ID_Usuario=id_docente).first()
    
    if usuario_a_baja:
        usuario_a_baja.Estado = False
        db.commit()
        
    db.close()
    return redirect(url_for('docentes'))

# -----------------------------------------------------  RF_32  -----------------------------------------------------
# RUTA: Pantalla y procesamiento para modificar docente
@app.route('/docentes/modificar/<int:id_docente>', methods=['GET', 'POST'])
def modificar_docente(id_docente):
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    # Traemos al docente junto con sus datos de usuario
    docente_a_modificar = db.query(Docente).filter_by(ID_Docente=id_docente).first()
    
    if request.method == 'POST':
        # Actualizamos la tabla Usuarios
        docente_a_modificar.usuario.NombreCompleto = request.form.get('nombre')
        docente_a_modificar.usuario.Matricula = request.form.get('matricula')
        docente_a_modificar.usuario.Correo = request.form.get('correo')
        
        # Actualizamos la tabla Docentes
        docente_a_modificar.Descripcion = request.form.get('descripcion')
        
        # Contraseña opcional
        nueva_contrasena = request.form.get('contrasena')
        if nueva_contrasena:
            docente_a_modificar.usuario.Contrasena = nueva_contrasena
            
        db.commit()
        db.close()
        return redirect(url_for('docentes'))
        
    db.close()
    return render_template('modificar_docente.html', docente=docente_a_modificar)

# -----------------------------------------------------  RF_29  -----------------------------------------------------
    # RUTA 1: Mostrar los grupos
# RUTA 1: Mostrar los grupos (Filtrados por Rol)
@app.route('/grupos')
def grupos():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    rol = session.get('rol')
    usuario_id = session.get('usuario_id')
    
    # Los estudiantes no entran a este panel, se van a su menú principal
    if rol == 'Estudiante':
        return redirect(url_for('dashboard'))
    
    criterio = request.args.get('buscar', '')
    db = SessionLocal()
    
    # 1. Buscamos los grupos activos
    query = db.query(Grupo).filter(Grupo.Estado == True)
    
    # Si es Docente, limitamos la búsqueda solo a sus grupos
    if rol == 'Docente':
        query = query.filter(Grupo.ID_Docente == usuario_id)
        
    if criterio:
        query = query.filter(
            (Grupo.Nombre.like(f"%{criterio}%")) | 
            (Grupo.CodigoInvitacion.like(f"%{criterio}%"))
        )
    lista_grupos = query.all()
    
    # 2. Llenar el select del formulario de Registro
    if rol == 'Administrador':
        # El admin ve a todos los maestros para poder asignar
        lista_docentes = db.query(Docente).join(Usuario).filter(Usuario.Estado == True).all()
    else:
        # El docente solo se ve a sí mismo en el formulario
        lista_docentes = db.query(Docente).filter_by(ID_Docente=usuario_id).all()
    
    db.close()
    return render_template('grupos.html', grupos=lista_grupos, docentes=lista_docentes)

# -----------------------------------------------------  RF_28  -----------------------------------------------------
@app.route('/grupos/registrar', methods=['POST'])
def registrar_grupo():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    
    # 1. Recopilar datos básicos y arreglar el error HY104 (convertir a entero)
    nombre_materia = request.form.get('nombre').strip().upper()
    id_docente_str = request.form.get('id_docente')
    
    if not id_docente_str:
        db.close()
        return f"<h1 style='color: red; text-align: center;'>Error: Por favor selecciona un docente.</h1><br><a href='/grupos'>Volver</a>"
        
    id_docente = int(id_docente_str)
    
    # 2. Procesar el horario múltiple y sacar las horas para el código
    dias_seleccionados = request.form.getlist('dias')
    horario_lista = []
    nombres_dias = {'Lu': 'lunes', 'Ma': 'martes', 'Mi': 'miercoles', 'Ju': 'jueves', 'Vi': 'viernes'}
    
    hora_inicio_codigo = "00"
    hora_fin_codigo = "00"
    
    for idx, dia_corto in enumerate(dias_seleccionados):
        dia_completo = nombres_dias[dia_corto]
        h_ini = request.form.get(f'{dia_completo}_inicio')
        h_fin = request.form.get(f'{dia_completo}_fin')
        
        if h_ini and h_fin:
            horario_lista.append(f"{dia_corto} {h_ini}-{h_fin}")
            # Guardamos la hora del primer día que haya elegido para el código
            if idx == 0:
                hora_inicio_codigo = h_ini[:2]
                hora_fin_codigo = h_fin[:2]
                
    horario_final_string = ", ".join(horario_lista) if horario_lista else "Sin horario asignado"
    
    # === 3. CONSTRUCCIÓN DEL CÓDIGO DE INVITACIÓN ===
    # A) Materia: Primeras 2 letras
    str_mat = nombre_materia[:2] if len(nombre_materia) >= 2 else nombre_materia.ljust(2, 'X')
    
    # B) Docente: Usando los nuevos campos exactos (Nombres y ApellidoPaterno)
    docente = db.query(Docente).filter_by(ID_Docente=id_docente).first()
    
    nombres_profe = (docente.usuario.Nombres or "XXX").strip().upper()
    apellido_pat_profe = (docente.usuario.ApellidoPaterno or "XXX").strip().upper()
    
    # Limpiamos acentos para que Velázquez sea VEZ y no VÉZ
    reemplazos = {'Á':'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U'}
    for a, b in reemplazos.items():
        nombres_profe = nombres_profe.replace(a, b)
        apellido_pat_profe = apellido_pat_profe.replace(a, b)
        
    # Primer nombre -> 2 primeras letras + última letra
    primer_nombre = nombres_profe.split()[0]
    str_nom = (primer_nombre[:2] + primer_nombre[-1]) if len(primer_nombre) >= 3 else primer_nombre.ljust(3, 'X')
    
    # Primer apellido -> 2 primeras letras + última letra
    primer_apellido = apellido_pat_profe.split()[0]
    str_ape = (primer_apellido[:2] + primer_apellido[-1]) if len(primer_apellido) >= 3 else primer_apellido.ljust(3, 'X')
    
    # C) Unimos todo: Ej. CADIOVEZ-0810
    codigo_generado = f"{str_mat}{str_nom}{str_ape}-{hora_inicio_codigo}{hora_fin_codigo}"
    
    # Por seguridad, si el mismo profe da dos clases iguales a la misma hora, le agregamos un número al final
    contador = 1
    codigo_final = codigo_generado
    while db.query(Grupo).filter_by(CodigoInvitacion=codigo_final).first():
        codigo_final = f"{codigo_generado}-{contador}"
        contador += 1
    # ================================================

    # 4. Guardar en base de datos
    try:
        nuevo_grupo = Grupo(
            CodigoInvitacion=codigo_final,
            Nombre=request.form.get('nombre'),
            Ciclo=request.form.get('ciclo'),
            EspacioFisico=request.form.get('espacio'), # Aquí cae el texto de "Espacio Virtual"
            Horario=horario_final_string,
            ID_Docente=id_docente,
            Estado=True
        )
        db.add(nuevo_grupo)
        db.commit()
    except Exception as e:
        db.rollback()
        return f"Error al guardar el grupo: {str(e)}"
    finally:
        db.close()
        
    return redirect(url_for('grupos'))

# -----------------------------------------------------  RF_31  -----------------------------------------------------
    # RUTA: Eliminar grupo (Borrado físico sin dejar rastro)
@app.route('/grupos/baja/<int:id_grupo>')
def baja_grupo(id_grupo):
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
    
    db = SessionLocal()
    grupo_a_eliminar = db.query(Grupo).filter_by(ID_Grupo=id_grupo).first()
    
    if grupo_a_eliminar:
        # Aquí usamos db.delete() para borrarlo por completo de SQL Server
        db.delete(grupo_a_eliminar)
        db.commit()
        
    db.close()
    return redirect(url_for('grupos'))

# -----------------------------------------------------  RF_30  -----------------------------------------------------
# RUTA: Pantalla y procesamiento para modificar grupo
@app.route('/grupos/modificar/<int:id_grupo>', methods=['GET', 'POST'])
def modificar_grupo(id_grupo):
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    grupo_a_modificar = db.query(Grupo).filter_by(ID_Grupo=id_grupo).first()
    docentes_activos = db.query(Docente).join(Usuario).filter(Usuario.Estado == True).all()
    
    if request.method == 'POST':
        grupo_a_modificar.Nombre = request.form.get('nombre').strip().upper()
        grupo_a_modificar.Ciclo = request.form.get('ciclo')
        grupo_a_modificar.EspacioFisico = request.form.get('espacio')
        grupo_a_modificar.ID_Docente = int(request.form.get('id_docente'))
        
        # Volvemos a procesar el horario
        dias_seleccionados = request.form.getlist('dias')
        horario_lista = []
        nombres_dias = {'Lu': 'lunes', 'Ma': 'martes', 'Mi': 'miercoles', 'Ju': 'jueves', 'Vi': 'viernes'}
        
        for dia_corto in dias_seleccionados:
            dia_completo = nombres_dias[dia_corto]
            h_ini = request.form.get(f'{dia_completo}_inicio')
            h_fin = request.form.get(f'{dia_completo}_fin')
            if h_ini and h_fin:
                horario_lista.append(f"{dia_corto} {h_ini}-{h_fin}")
                
        grupo_a_modificar.Horario = ", ".join(horario_lista) if horario_lista else "Sin horario asignado"
        
        # Nota: El Código de Invitación NO se recalcula aquí para evitar
        # que los alumnos que ya lo tienen se queden sin acceso si le cambias el nombre a la materia.
        
        db.commit()
        db.close()
        return redirect(url_for('grupos'))
    
    # Lógica para "desarmar" el horario y mandarlo a la vista (GET)
    horario_dict = {}
    if grupo_a_modificar.Horario and grupo_a_modificar.Horario != "Sin horario asignado":
        partes = grupo_a_modificar.Horario.split(", ")
        for parte in partes:
            if " " in parte and "-" in parte:
                dia, horas = parte.split(" ")
                ini, fin = horas.split("-")
                horario_dict[dia] = {'ini': ini, 'fin': fin}
                
    db.close()
    return render_template('modificar_grupo.html', grupo=grupo_a_modificar, docentes=docentes_activos, horario=horario_dict)

# -----------------------------------------------------  RF_29  -----------------------------------------------------
@app.route('/buscar_cursos')
def buscar_cursos():
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    criterio = request.args.get('q', '')
    db = SessionLocal()
    
    query = db.query(Grupo).filter(Grupo.Estado == True)
    if criterio:
        query = query.filter(Grupo.Nombre.like(f"%{criterio}%"))
        
    grupos_disponibles = query.all()
    db.close()
    
    return render_template('buscar_cursos.html', grupos=grupos_disponibles)

# -----------------------------------------------------  RF_02  -----------------------------------------------------
@app.route('/unirse_curso', methods=['POST'])
def unirse_curso():
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    id_grupo = request.form.get('id_grupo')
    codigo_ingresado = request.form.get('codigo_invitacion')
    
    # BLINDAJE: Quitamos espacios accidentales y lo forzamos a mayúsculas
    if codigo_ingresado:
        codigo_ingresado = codigo_ingresado.strip().upper()
    
    db = SessionLocal()
    
    # 1. Asegurarnos de que el ID no cause conflictos
    try:
        id_grupo = int(id_grupo)
    except:
        db.close()
        return "<h1 style='color: red; text-align: center;'>Error: ID de grupo inválido.</h1><br><a href='/buscar_cursos'>Volver</a>"
        
    # 2. Validar grupo y código
    grupo = db.query(Grupo).filter_by(ID_Grupo=id_grupo, CodigoInvitacion=codigo_ingresado).first()
    
    if not grupo:
        db.close()
        return f"<h1 style='color: red; text-align: center;'>Error: El código '{codigo_ingresado}' es incorrecto.</h1><br><a href='/buscar_cursos'>Volver a intentar</a>"
        
    # GUARDAMOS EL NOMBRE ANTES DE CERRAR LA SESIÓN PARA EVITAR EL ERROR DETACHEDINSTANCE
    nombre_grupo = grupo.Nombre
        
    # 3. Verificamos si ya está inscrito
    ya_inscrito = db.query(GrupoEstudiante).filter_by(ID_Estudiante=session['usuario_id'], ID_Grupo=id_grupo).first()
    if ya_inscrito:
        db.close()
        return f"<h1 style='color: orange; text-align: center;'>Aviso: Ya te encuentras en el grupo '{nombre_grupo}'.</h1><br><a href='/dashboard'>Ir a mis cursos</a>"
        
    # 4. Inscripción real
    try:
        nueva_inscripcion = GrupoEstudiante(ID_Estudiante=session['usuario_id'], ID_Grupo=id_grupo)
        db.add(nueva_inscripcion)
        db.commit()
    except Exception as e:
        db.rollback()
        return f"<h1 style='color: red; text-align: center;'>Error de Base de Datos:</h1><p style='text-align: center;'>{str(e)}</p><br><a href='/buscar_cursos'>Volver</a>"
    finally:
        db.close()
    
    # 5. PANTALLA DE ÉXITO VISUAL (Usando la variable de texto guardada)
    return f"""
    <div style="font-family: sans-serif; text-align: center; margin-top: 50px;">
        <h1 style='color: #16a34a;'>¡Inscripción Exitosa!</h1>
        <p>Te has unido correctamente al grupo <strong>{nombre_grupo}</strong>.</p>
        <a href='/dashboard' style="display: inline-block; background-color: #0284c7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px;">Ir a mis cursos</a>
    </div>
    """

# -----------------------------------------------------  RF_29  -----------------------------------------------------
# RUTA: Entrar al aula virtual de un grupo específico
@app.route('/grupo/<int:id_grupo>')
def ver_grupo(id_grupo):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
        
    db = SessionLocal()
    grupo_actual = db.query(Grupo).filter_by(ID_Grupo=id_grupo).first()
    
    if not grupo_actual:
        db.close()
        return redirect(url_for('dashboard'))
        
    tareas_entregadas_ids = []
    promedio_alumno = None
    promedios_docente = {}
    
    tareas_del_grupo = db.query(Tarea).filter_by(ID_Grupo=id_grupo, Estado=True).all()
    ids_tareas = [t.ID_Tarea for t in tareas_del_grupo]

    actividades_del_grupo = db.query(Actividad).filter_by(ID_Grupo=id_grupo, Estado=True).order_by(Actividad.FechaPublicacion.desc()).all()
    ids_acts = [a.ID_Actividad for a in actividades_del_grupo]

    # SOLUCIÓN: Agrupamos los filtros en una lista para no mandar "False" a la consulta
    filtros_calif = []
    if ids_tareas: filtros_calif.append(Calificacion.ID_Tarea.in_(ids_tareas))
    if ids_acts: filtros_calif.append(Calificacion.ID_Actividad.in_(ids_acts))

    if session.get('rol') == 'Estudiante':
        inscrito = db.query(GrupoEstudiante).filter_by(ID_Estudiante=session['usuario_id'], ID_Grupo=id_grupo).first()
        if not inscrito:
            db.close()
            return redirect(url_for('dashboard'))
            
        entregas = db.query(Entrega.ID_Tarea).filter_by(ID_Estudiante=session['usuario_id']).all()
        tareas_entregadas_ids = [e[0] for e in entregas]
        
        # Evaluamos usando los filtros seguros
        if filtros_calif:
            notas = db.query(Calificacion).filter(
                Calificacion.ID_Estudiante == session['usuario_id'],
                or_(*filtros_calif)
            ).all()
            
            if notas:
                suma = sum(float(n.Puntuacion) for n in notas if n.Puntuacion is not None)
                promedio_alumno = round(suma / len(notas), 1)

    elif session.get('rol') in ['Docente', 'Administrador']:
        if filtros_calif:
            notas = db.query(Calificacion).filter(or_(*filtros_calif)).all()
            
            sumas = {}
            conteos = {}
            for n in notas:
                if n.Puntuacion is not None:
                    sumas[n.ID_Estudiante] = sumas.get(n.ID_Estudiante, 0) + float(n.Puntuacion)
                    conteos[n.ID_Estudiante] = conteos.get(n.ID_Estudiante, 0) + 1
            
            for est_id in sumas:
                promedios_docente[est_id] = round(sumas[est_id] / conteos[est_id], 1)
            
    integrantes = []
    for inscripcion in grupo_actual.estudiantes_inscritos:
        if inscripcion.usuario.Estado:
            integrantes.append(inscripcion.usuario)
            
    db.close()
    
    return render_template('grupo_detalle.html', 
                           grupo=grupo_actual, 
                           integrantes=integrantes, 
                           tareas=tareas_del_grupo, 
                           tareas_entregadas_ids=tareas_entregadas_ids,
                           promedio_alumno=promedio_alumno,
                           promedios_docente=promedios_docente,
                           actividades=actividades_del_grupo)

# -----------------------------------------------------  RF_05  -----------------------------------------------------
@app.route('/grupo/salir/<int:id_grupo>')
def salir_grupo(id_grupo):
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    # Por seguridad, verificamos que quien intenta salir sea realmente un estudiante
    if session.get('rol') != 'Estudiante':
        return redirect(url_for('dashboard'))
        
    db = SessionLocal()
    
    # Buscamos el registro en la tabla puente Grupo_Estudiantes
    inscripcion = db.query(GrupoEstudiante).filter_by(
        ID_Estudiante=session['usuario_id'], 
        ID_Grupo=id_grupo
    ).first()
    
    if inscripcion:
        # Hacemos un borrado físico de la inscripción
        db.delete(inscripcion)
        db.commit()
        
    db.close()
    
    # Lo regresamos a su menú principal, donde ya no verá el curso
    return redirect(url_for('dashboard'))


    # RUTA: Mi Perfil
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    rol = session.get('rol')
    usuario = db.query(Usuario).filter_by(ID_Usuario=session['usuario_id']).first()
    
    # Si es docente, buscamos también su descripción
    docente_info = None
    if rol == 'Docente':
        docente_info = db.query(Docente).filter_by(ID_Docente=session['usuario_id']).first()
        
    if request.method == 'POST':
        # 1. Procesar la foto (Para Estudiantes y Docentes)
        if 'foto' in request.files:
            foto_file = request.files['foto']
            if foto_file.filename != '':
                # Limpiamos el nombre del archivo y le pegamos el ID para que no haya nombres repetidos
                filename = secure_filename(foto_file.filename)
                nuevo_nombre_foto = f"usr_{usuario.ID_Usuario}_{filename}"
                ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER'], nuevo_nombre_foto)
                
                foto_file.save(ruta_guardado)
                usuario.FotoPerfil = nuevo_nombre_foto
                session['foto'] = nuevo_nombre_foto # Actualizamos la sesión para que cambie al instante
                
        # 2. Procesar la descripción (Solo para Docentes)
        if rol == 'Docente' and docente_info:
            nueva_descripcion = request.form.get('descripcion')
            if nueva_descripcion is not None:
                docente_info.Descripcion = nueva_descripcion
                
        db.commit()
        db.close()
        return redirect(url_for('perfil'))
        
    db.close()
    return render_template('perfil.html', usuario=usuario, docente=docente_info)

    # ==========================================
# MÓDULO DE CHAT
# ==========================================
# -----------------------------------------------------  RF_25  -----------------------------------------------------
@app.route('/chat')
def chat_inicio():
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    if session.get('rol') == 'Administrador': return redirect(url_for('dashboard')) # Privacidad
    
    db = SessionLocal()
    usuario_id = session['usuario_id']
    
    # Obtener el historial para armar la lista de contactos recientes
    mensajes = db.query(Mensaje).filter(
        or_(Mensaje.ID_Remitente == usuario_id, Mensaje.ID_Destinatario == usuario_id)
    ).order_by(Mensaje.FechaEnvio.desc()).all()
    
    contactos_ids = []
    for m in mensajes:
        oid = m.ID_Destinatario if m.ID_Remitente == usuario_id else m.ID_Remitente
        if oid not in contactos_ids: contactos_ids.append(oid)
            
    contactos = [db.query(Usuario).filter_by(ID_Usuario=oid).first() for oid in contactos_ids]
    
    # Lista de todos para poder iniciar un chat nuevo
    todos_usuarios = db.query(Usuario).filter(
        Usuario.Estado == True, 
        Usuario.Rol != 'Administrador', 
        Usuario.ID_Usuario != usuario_id
    ).all()
    
    db.close()
    return render_template('chat.html', contactos=contactos, todos_usuarios=todos_usuarios, chat_actual=None)

# -----------------------------------------------------  RF_25  -----------------------------------------------------
@app.route('/chat/<int:id_otro>')
def chat_conversacion(id_otro):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    if session.get('rol') == 'Administrador': return redirect(url_for('dashboard'))
    
    db = SessionLocal()
    usuario_id = session['usuario_id']
    
    # Lista de contactos (Misma lógica que arriba)
    mensajes = db.query(Mensaje).filter(
        or_(Mensaje.ID_Remitente == usuario_id, Mensaje.ID_Destinatario == usuario_id)
    ).order_by(Mensaje.FechaEnvio.desc()).all()
    
    contactos_ids = []
    for m in mensajes:
        oid = m.ID_Destinatario if m.ID_Remitente == usuario_id else m.ID_Remitente
        if oid not in contactos_ids: contactos_ids.append(oid)
            
    # Si es un chat nuevo, lo agregamos a la lista de contactos visual
    if id_otro not in contactos_ids: contactos_ids.insert(0, id_otro)
    contactos = [db.query(Usuario).filter_by(ID_Usuario=oid).first() for oid in contactos_ids]
    
    todos_usuarios = db.query(Usuario).filter(Usuario.Estado==True, Usuario.Rol!='Administrador', Usuario.ID_Usuario!=usuario_id).all()
    
    # Cargar los mensajes de esta conversación en específico
    conversacion = db.query(Mensaje).filter(
        or_(
            and_(Mensaje.ID_Remitente == usuario_id, Mensaje.ID_Destinatario == id_otro),
            and_(Mensaje.ID_Remitente == id_otro, Mensaje.ID_Destinatario == usuario_id)
        )
    ).order_by(Mensaje.FechaEnvio.asc()).all()
    
    otro_usuario = db.query(Usuario).filter_by(ID_Usuario=id_otro).first()
    
    db.close()
    return render_template('chat.html', contactos=contactos, todos_usuarios=todos_usuarios, chat_actual=otro_usuario, conversacion=conversacion)

# -----------------------------------------------------  RF_24  -----------------------------------------------------
@app.route('/chat/enviar', methods=['POST'])
def enviar_mensaje():
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    id_destinatario = request.form.get('id_destinatario')
    contenido = request.form.get('contenido')
    
    if id_destinatario and contenido:
        db = SessionLocal()
        nuevo_msg = Mensaje(
            ID_Remitente=session['usuario_id'],
            ID_Destinatario=int(id_destinatario),
            Contenido=contenido.strip()
        )
        db.add(nuevo_msg)
        db.commit()
        db.close()
        
    return redirect(url_for('chat_conversacion', id_otro=id_destinatario))

# -----------------------------------------------------  RF_27  -----------------------------------------------------
@app.route('/chat/eliminar/<int:id_mensaje>', methods=['POST'])
def eliminar_mensaje(id_mensaje):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    db = SessionLocal()
    # Buscamos el mensaje asegurando que le pertenezca al usuario actual
    msg = db.query(Mensaje).filter_by(ID_Mensaje=id_mensaje, ID_Remitente=session['usuario_id']).first()
    
    if msg:
        id_destinatario = msg.ID_Destinatario
        db.delete(msg)
        db.commit()
        db.close()
        return redirect(url_for('chat_conversacion', id_otro=id_destinatario))
        
    db.close()
    return redirect(url_for('chat_inicio'))

# -----------------------------------------------------  RF_26  -----------------------------------------------------
@app.route('/chat/editar/<int:id_mensaje>', methods=['POST'])
def editar_mensaje(id_mensaje):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    nuevo_contenido = request.form.get('nuevo_contenido')
    
    if nuevo_contenido:
        db = SessionLocal()
        msg = db.query(Mensaje).filter_by(ID_Mensaje=id_mensaje, ID_Remitente=session['usuario_id']).first()
        
        if msg:
            id_destinatario = msg.ID_Destinatario
            msg.Contenido = nuevo_contenido.strip()
            db.commit()
            db.close()
            return redirect(url_for('chat_conversacion', id_otro=id_destinatario))
            
        db.close()
    return redirect(url_for('chat_inicio'))

# -----------------------------------------------------  RF_09  -----------------------------------------------------
# RUTA: Crear una nueva tarea dentro de un grupo
@app.route('/grupo/<int:id_grupo>/tarea/crear', methods=['POST'])
def crear_tarea(id_grupo):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    if session.get('rol') == 'Estudiante':
        return redirect(url_for('ver_grupo', id_grupo=id_grupo))
        
    titulo = request.form.get('titulo')
    fecha_limite_str = request.form.get('fecha_limite')
    
    descripcion = request.form.get('descripcion')
    if not descripcion or descripcion.strip() == "":
        descripcion = None
        
    if titulo and fecha_limite_str:
        db = SessionLocal()
        
        nombre_archivo = None 
        if 'archivo' in request.files:
            archivo_file = request.files['archivo']
            if archivo_file.filename != '':
                filename = secure_filename(archivo_file.filename)
                if filename.lower().endswith(('.jpg', '.jpeg')):
                    nombre_archivo = f"grupo{id_grupo}tarea{filename}"
                    ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER_TAREAS'], nombre_archivo)
                    archivo_file.save(ruta_guardado)
        
        fecha_limite = datetime.strptime(fecha_limite_str, '%Y-%m-%dT%H:%M')
        fecha_actual = datetime.utcnow()
        
        # SOLUCIÓN DEFINITIVA: Inserción SQL Directa
        # Al escribir el INSERT manualmente, evitamos que el driver viejo de SQL Server colapse.
        consulta = text("""
            INSERT INTO Tareas (ID_Grupo, Titulo, Descripcion, ArchivosAdicionales, FechaAsignacion, FechaLimite, Estado)
            VALUES (:grupo, :tit, :desc, :arch, :fasig, :flim, 1)
        """)
        
        # Ejecutamos la consulta pasando las fechas convertidas a texto ('YYYY-MM-DD HH:MM:SS')
        db.execute(consulta, {
            "grupo": id_grupo,
            "tit": titulo[:150],
            "desc": descripcion,
            "arch": nombre_archivo,
            "fasig": fecha_actual.strftime('%Y-%m-%d %H:%M:%S'), 
            "flim": fecha_limite.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        db.commit()
        db.close()
        
    return redirect(url_for('ver_grupo', id_grupo=id_grupo))

# -----------------------------------------------------  RF_14  -----------------------------------------------------
  # RUTA: Vista Global de Tareas (Menú Lateral)
@app.route('/tareas')
def tareas_globales():
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    db = SessionLocal()
    rol = session.get('rol')
    usuario_id = session['usuario_id']
    criterio = request.args.get('buscar', '').strip()
    tareas_mostrar = []
    
    if rol == 'Estudiante':
        inscripciones = db.query(GrupoEstudiante).filter_by(ID_Estudiante=usuario_id).all()
        ids_grupos = [insc.ID_Grupo for insc in inscripciones]
        
        # -----------------------------------------------------  RF_10  -----------------------------------------------------
        # Obtenemos los IDs de las tareas que ya entregó
        entregas = db.query(Entrega.ID_Tarea).filter_by(ID_Estudiante=usuario_id).all()
        entregadas_ids = [e[0] for e in entregas]
        
        if ids_grupos:
            query = db.query(Tarea).filter(Tarea.ID_Grupo.in_(ids_grupos), Tarea.Estado == True)
            
            # NUEVO: Si ya entregó algunas, las filtramos para que no aparezcan
            if entregadas_ids:
                query = query.filter(Tarea.ID_Tarea.notin_(entregadas_ids))
                
            if criterio:
                query = query.filter(Tarea.Titulo.like(f"%{criterio}%"))
            tareas_mostrar = query.order_by(Tarea.FechaLimite.asc()).all()
            
    elif rol == 'Docente':
        grupos_docente = db.query(Grupo).filter_by(ID_Docente=usuario_id).all()
        ids_grupos = [g.ID_Grupo for g in grupos_docente]
        
        if ids_grupos:
            query = db.query(Tarea).filter(Tarea.ID_Grupo.in_(ids_grupos), Tarea.Estado == True)
            if criterio:
                query = query.filter(Tarea.Titulo.like(f"%{criterio}%"))
            tareas_mostrar = query.order_by(Tarea.FechaLimite.asc()).all()
            
    tareas_por_grupo = {}
    for tarea in tareas_mostrar:
        nombre_grupo = tarea.grupo.Nombre 
        if nombre_grupo not in tareas_por_grupo:
            tareas_por_grupo[nombre_grupo] = []
        tareas_por_grupo[nombre_grupo].append(tarea)
            
    db.close()
    return render_template('tareas.html', tareas_por_grupo=tareas_por_grupo, criterio=criterio)


# RUTA: Ver detalles de la tarea y sus entregas
@app.route('/tarea/<int:id_tarea>')
def ver_tarea(id_tarea):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    db = SessionLocal()
    # Cargamos la tarea y el grupo
    tarea_actual = db.query(Tarea).options(joinedload(Tarea.grupo)).filter_by(ID_Tarea=id_tarea).first()
    
    if not tarea_actual:
        db.close()
        return redirect(url_for('dashboard'))
        
    mi_entrega = None
    entregas_recibidas = []
    
    # Si es estudiante, buscamos solo su entrega
    if session.get('rol') == 'Estudiante':
        mi_entrega = db.query(Entrega).filter_by(ID_Tarea=id_tarea, ID_Estudiante=session['usuario_id']).first()
    
    # Si es docente, buscamos TODAS las entregas de sus alumnos
    elif session.get('rol') == 'Docente':
        entregas_recibidas = db.query(Entrega).options(joinedload(Entrega.estudiante)).filter_by(ID_Tarea=id_tarea).order_by(Entrega.FechaHoraEntrega.desc()).all()

    comentarios = db.query(ComentarioTarea).options(joinedload(ComentarioTarea.autor)).filter_by(ID_Tarea=id_tarea).order_by(ComentarioTarea.Fecha.asc()).all()
    
    calificaciones_bd = db.query(Calificacion).filter_by(ID_Tarea=id_tarea).all()
    notas_dict = {c.ID_Estudiante: c for c in calificaciones_bd} # Diccionario para buscar rápido en el HTML
        
    db.close()
    return render_template('tarea_detalle.html', tarea=tarea_actual, mi_entrega=mi_entrega, entregas=entregas_recibidas, comentarios=comentarios, notas=notas_dict)
 
 # -----------------------------------------------------  RF_33 y RF_35  -----------------------------------------------------
# RUTA: Subir o Modificar entrega (Múltiples archivos)
@app.route('/tarea/<int:id_tarea>/entregar', methods=['POST'])
def subir_entrega(id_tarea):
    if 'usuario_id' not in session or session.get('rol') != 'Estudiante':
        return redirect(url_for('inicio'))
        
    # getlist() atrapa TODOS los archivos que el alumno seleccione
    archivos = request.files.getlist('archivo_entrega')
    nombres_guardados = []
    
    for archivo in archivos:
        if archivo and archivo.filename != '':
            filename = secure_filename(archivo.filename)
            if filename.lower().endswith(('.jpg', '.jpeg')):
                # Usamos UUID para generar un código único corto y que no choquen los nombres
                unico = str(uuid.uuid4())[:6]
                nombre_archivo = f"t{id_tarea}e{session['usuario_id']}{unico}_{filename}"
                ruta_guardado = os.path.join(app.config['UPLOAD_FOLDER_ENTREGAS'], nombre_archivo)
                archivo.save(ruta_guardado)
                nombres_guardados.append(nombre_archivo)
                
    # Si el usuario subió archivos válidos, actualizamos o insertamos
    if nombres_guardados:
        string_archivos = "|".join(nombres_guardados) # Los unimos con un "pipe" ( | )
        
        db = SessionLocal()
        fecha_actual = datetime.utcnow()
        mi_entrega = db.query(Entrega).filter_by(ID_Tarea=id_tarea, ID_Estudiante=session['usuario_id']).first()
        
        if mi_entrega:
            # Si ya existía (MODIFICAR), solo sobreescribimos los archivos y la fecha
            mi_entrega.ArchivoURL = string_archivos
            mi_entrega.FechaHoraEntrega = fecha_actual
            db.commit()
        else:
            # Si es NUEVA
            consulta = text("""
                INSERT INTO Entregas (ID_Tarea, ID_Estudiante, ArchivoURL, FechaHoraEntrega, Estado)
                VALUES (:tar, :est, :arch, :fech, 1)
            """)
            db.execute(consulta, {
                "tar": id_tarea,
                "est": session['usuario_id'],
                "arch": string_archivos,
                "fech": fecha_actual.strftime('%Y-%m-%d %H:%M:%S')
            })
            db.commit()
        db.close()
                
    return redirect(url_for('ver_tarea', id_tarea=id_tarea))

# -----------------------------------------------------  RF_36  -----------------------------------------------------
# RUTA: Eliminar Entrega (Deshacer)
@app.route('/tarea/<int:id_tarea>/eliminar_entrega', methods=['POST'])
def eliminar_entrega(id_tarea):
    if 'usuario_id' not in session or session.get('rol') != 'Estudiante':
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    # Buscamos la entrega de este alumno
    mi_entrega = db.query(Entrega).filter_by(ID_Tarea=id_tarea, ID_Estudiante=session['usuario_id']).first()
    
    if mi_entrega:
        db.delete(mi_entrega) # La borramos de la base de datos
        db.commit()
        
    db.close()
    # Al recargar, como la entrega ya no existe, en todos lados aparecerá "Pendiente"
    return redirect(url_for('ver_tarea', id_tarea=id_tarea))

    # RUTA: Eliminar Tarea (Borrado Lógico)
@app.route('/tarea/<int:id_tarea>/eliminar', methods=['POST'])
def eliminar_tarea(id_tarea):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    tarea = db.query(Tarea).filter_by(ID_Tarea=id_tarea).first()
    
    if tarea:
        id_grupo = tarea.ID_Grupo
        tarea.Estado = False # La ocultamos en lugar de borrarla para no romper entregas previas
        db.commit()
        db.close()
        return redirect(url_for('ver_grupo', id_grupo=id_grupo))
        
    db.close()
    return redirect(url_for('dashboard'))

# -----------------------------------------------------  RF_12  -----------------------------------------------------
# RUTA: Editar Tarea
@app.route('/tarea/<int:id_tarea>/editar', methods=['POST'])
def editar_tarea(id_tarea):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return redirect(url_for('inicio'))
        
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    fecha_limite_str = request.form.get('fecha_limite')
    
    db = SessionLocal()
    tarea = db.query(Tarea).filter_by(ID_Tarea=id_tarea).first()
    
    if tarea and titulo and fecha_limite_str:
        id_grupo = tarea.ID_Grupo
        tarea.Titulo = titulo[:150]
        tarea.Descripcion = descripcion if descripcion and descripcion.strip() != "" else None
        tarea.FechaLimite = datetime.strptime(fecha_limite_str, '%Y-%m-%dT%H:%M')
        db.commit()
        db.close()
        return redirect(url_for('ver_grupo', id_grupo=id_grupo))
        
    db.close()
    return redirect(url_for('dashboard'))

# -----------------------------------------------------  RF_13  -----------------------------------------------------
    # RUTA: Publicar un comentario público en la tarea
@app.route('/tarea/<int:id_tarea>/comentar', methods=['POST'])
def comentar_tarea(id_tarea):
    # Solo los docentes pueden publicar avisos aquí
    if 'usuario_id' not in session or session.get('rol') != 'Docente':
        return redirect(url_for('ver_tarea', id_tarea=id_tarea))
        
    contenido = request.form.get('contenido')
    
    if contenido and contenido.strip() != "":
        db = SessionLocal()
        consulta = text("""
            INSERT INTO ComentariosTarea (ID_Tarea, ID_Usuario, Contenido, Fecha)
            VALUES (:tar, :usu, :cont, :fech)
        """)
        db.execute(consulta, {
            "tar": id_tarea,
            "usu": session['usuario_id'],
            "cont": contenido.strip(),
            "fech": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
        db.commit()
        db.close()
        
    return redirect(url_for('ver_tarea', id_tarea=id_tarea))

# -----------------------------------------------------  RF_19  -----------------------------------------------------
    # RUTA: Guardar o actualizar la calificación de un alumno
@app.route('/tarea/<int:id_tarea>/calificar/<int:id_estudiante>', methods=['POST'])
def calificar_tarea(id_tarea, id_estudiante):
    if 'usuario_id' not in session or session.get('rol') != 'Docente':
        return redirect(url_for('inicio'))

    puntuacion = request.form.get('puntuacion')
    retro = request.form.get('retroalimentacion')

    db = SessionLocal()
    calif = db.query(Calificacion).filter_by(ID_Tarea=id_tarea, ID_Estudiante=id_estudiante).first()
    fecha_actual = datetime.utcnow()

    if calif:
        # Si ya lo había calificado, actualizamos
        calif.Puntuacion = puntuacion
        calif.Retroalimentacion = retro
        calif.FechaCalificacion = fecha_actual
        db.commit()
    else:
        # Si es la primera vez, insertamos con SQL puro para evitar el error HY104
        consulta = text("""
            INSERT INTO Calificaciones (ID_Estudiante, ID_Tarea, Puntuacion, Retroalimentacion, FechaCalificacion)
            VALUES (:est, :tar, :punt, :retro, :fech)
        """)
        db.execute(consulta, {
            "est": id_estudiante,
            "tar": id_tarea,
            "punt": puntuacion,
            "retro": retro,
            "fech": fecha_actual.strftime('%Y-%m-%d %H:%M:%S')
        })
        db.commit()
        
    db.close()
    return redirect(url_for('ver_tarea', id_tarea=id_tarea))


# RUTA: Vista Global de Calificaciones (Menú Lateral del Alumno)
@app.route('/calificaciones')
def mis_calificaciones():
    if 'usuario_id' not in session or session.get('rol') != 'Estudiante':
        return redirect(url_for('dashboard'))

    db = SessionLocal()
    
    # SOLUCIÓN: Encadenamos joinedload para traer la Calificación -> Tarea -> Grupo
    mis_notas = db.query(Calificacion).options(
        joinedload(Calificacion.tarea).joinedload(Tarea.grupo)
    ).filter_by(ID_Estudiante=session['usuario_id']).filter(Calificacion.ID_Tarea != None).order_by(Calificacion.FechaCalificacion.desc()).all()
    
    db.close()
    
    return render_template('calificaciones.html', calificaciones=mis_notas)

    # RUTA: Pantalla para armar un examen
@app.route('/grupo/<int:id_grupo>/crear_examen')
def crear_examen(id_grupo):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return redirect(url_for('inicio'))
    db = SessionLocal()
    grupo = db.query(Grupo).filter_by(ID_Grupo=id_grupo).first()
    db.close()
    return render_template('crear_examen.html', grupo=grupo)

# API: Guardar el examen armado en la base de datos
@app.route('/api/grupo/<int:id_grupo>/guardar_examen', methods=['POST'])
def guardar_examen(id_grupo):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return jsonify({"error": "No autorizado"}), 403
        
    db = SessionLocal()
    try:
        data = request.json
        
        fecha_limite_str = data.get('fecha_limite')
        fecha_lim = datetime.strptime(fecha_limite_str, '%Y-%m-%dT%H:%M') if fecha_limite_str else None
        
        # 1. Guardamos la actividad principal con el ORM (Funciona porque no usa campos TEXT)
        nueva_act = Actividad(
            ID_Grupo=id_grupo, 
            Titulo=data['titulo'], 
            TiempoMinutos=int(data['tiempo']),
            FechaLimite=fecha_lim
        )
        db.add(nueva_act)
        db.flush() # Guardamos temporalmente en la memoria para que SQL Server nos asigne un ID_Actividad
        
        # 2. Guardamos las preguntas y sus incisos con SQL puro (Para evitar el error HY104)
        for p_data in data['preguntas']:
            
            # Usamos OUTPUT INSERTED.ID_Pregunta para recuperar el ID que SQL Server acaba de crear
            consulta_preg = text("""
                INSERT INTO PreguntasExamen (ID_Actividad, TextoPregunta)
                OUTPUT INSERTED.ID_Pregunta
                VALUES (:act, :txt)
            """)
            res_preg = db.execute(consulta_preg, {
                "act": nueva_act.ID_Actividad,
                "txt": p_data['texto']
            })
            id_preg = res_preg.fetchone()[0] # Capturamos el ID
            
            # 3. Guardamos los incisos enlazados a esa pregunta
            for i, op_texto in enumerate(p_data['opciones']):
                es_correcta = 1 if i == int(p_data['correctaIndex']) else 0
                consulta_op = text("""
                    INSERT INTO OpcionesPregunta (ID_Pregunta, TextoOpcion, EsCorrecta)
                    VALUES (:preg, :txt, :corr)
                """)
                db.execute(consulta_op, {
                    "preg": id_preg,
                    "txt": op_texto,
                    "corr": es_correcta
                })
                
        db.commit() # Si todo sale bien, confirmamos y guardamos todo junto
        db.close()
        return jsonify({"status": "success"})
        
    except Exception as e:
        db.rollback() # Si falla, deshacemos todo para no dejar un examen a medias
        db.close()
        print(f"Error crítico al guardar examen: {e}")
        return jsonify({"error": str(e)}), 500
    

    # RUTA: Vista Global de Actividades (Menú Lateral)
@app.route('/actividades')
def actividades_globales():
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    db = SessionLocal()
    rol = session.get('rol')
    usuario_id = session['usuario_id']
    actividades_mostrar = []
    
    if rol == 'Estudiante':
        # Traemos todos los grupos del alumno
        inscripciones = db.query(GrupoEstudiante).filter_by(ID_Estudiante=usuario_id).all()
        ids_grupos = [insc.ID_Grupo for insc in inscripciones]
        
        if ids_grupos:
            # Traemos las actividades e incluimos la información del grupo para que no falle el HTML (joinedload)
            actividades_mostrar = db.query(Actividad).options(joinedload(Actividad.grupo)).filter(Actividad.ID_Grupo.in_(ids_grupos), Actividad.Estado == True).order_by(Actividad.FechaLimite.asc()).all()
            
    # Agrupamos por materia (igual que en tareas)
    act_por_grupo = {}
    for act in actividades_mostrar:
        nombre_grupo = act.grupo.Nombre 
        if nombre_grupo not in act_por_grupo:
            act_por_grupo[nombre_grupo] = []
        act_por_grupo[nombre_grupo].append(act)
            
    db.close()
    return render_template('actividades.html', actividades_por_grupo=act_por_grupo)

# -----------------------------------------------------  RF_16  -----------------------------------------------------
    # RUTA: Pantalla para realizar o ver resultados de una actividad
@app.route('/actividad/<int:id_actividad>')
def ver_actividad(id_actividad):
    if 'usuario_id' not in session: return redirect(url_for('inicio'))
    
    db = SessionLocal()
    actividad = db.query(Actividad).options(joinedload(Actividad.grupo), joinedload(Actividad.preguntas).joinedload(PreguntaExamen.opciones)).filter_by(ID_Actividad=id_actividad).first()
    
    if not actividad:
        db.close()
        return redirect(url_for('dashboard'))
        
    mi_calificacion = None
    calificaciones_todos = []
    
    if session.get('rol') == 'Estudiante':
        # Revisamos si el alumno ya hizo este examen
        mi_calificacion = db.query(Calificacion).filter_by(ID_Estudiante=session['usuario_id'], ID_Actividad=id_actividad).first()
    else:
        # El maestro puede ver quién ya lo terminó
        calificaciones_todos = db.query(Calificacion).options(joinedload(Calificacion.estudiante)).filter_by(ID_Actividad=id_actividad).all()
        
    db.close()
    return render_template('actividad_detalle.html', actividad=actividad, mi_calificacion=mi_calificacion, calificaciones=calificaciones_todos)

# -----------------------------------------------------  RF_19  -----------------------------------------------------
# API: Auto-Calificar el Examen al terminar
@app.route('/api/actividad/<int:id_actividad>/evaluar', methods=['POST'])
def evaluar_actividad(id_actividad):
    if 'usuario_id' not in session or session.get('rol') != 'Estudiante':
        return jsonify({"error": "No autorizado"}), 403

    db = SessionLocal()
    try:
        # 1. Verificamos que no lo haya hecho ya (para evitar trampas)
        existe = db.query(Calificacion).filter_by(ID_Estudiante=session['usuario_id'], ID_Actividad=id_actividad).first()
        if existe:
            db.close()
            return jsonify({"error": "Ya realizaste este examen"}), 400

        data = request.json
        respuestas_alumno = data.get('respuestas', {})
        actividad = db.query(Actividad).options(joinedload(Actividad.preguntas).joinedload(PreguntaExamen.opciones)).filter_by(ID_Actividad=id_actividad).first()

        # 2. Comparamos con los incisos correctos
        correctas = 0
        total = len(actividad.preguntas)

        for preg in actividad.preguntas:
            op_correcta = next((op for op in preg.opciones if op.EsCorrecta), None)
            if op_correcta and str(preg.ID_Pregunta) in respuestas_alumno:
                if str(respuestas_alumno[str(preg.ID_Pregunta)]) == str(op_correcta.ID_Opcion):
                    correctas += 1

        puntuacion = (correctas / total) * 100 if total > 0 else 0

        # 3. Guardamos la calificación automáticamente
        fecha_actual = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        consulta = text("""
            INSERT INTO Calificaciones (ID_Estudiante, ID_Actividad, Puntuacion, Retroalimentacion, FechaCalificacion)
            VALUES (:est, :act, :punt, :retro, :fech)
        """)
        db.execute(consulta, {
            "est": session['usuario_id'],
            "act": id_actividad,
            "punt": round(puntuacion, 2),
            "retro": f"Auto-calificado por el sistema. Obtuviste {correctas} aciertos de {total} preguntas.",
            "fech": fecha_actual
        })
        db.commit()
        db.close()

        return jsonify({"status": "success"})
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({"error": str(e)}), 500
    
# RUTA: Eliminar Actividad (Borrado DEFINITIVO de la base de datos)
@app.route('/actividad/<int:id_actividad>/eliminar', methods=['POST'])
def eliminar_actividad(id_actividad):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    try:
        act = db.query(Actividad).filter_by(ID_Actividad=id_actividad).first()
        if act:
            id_grupo = act.ID_Grupo
            
            # 1. Borramos las calificaciones asociadas a esta actividad para no romper relaciones
            db.execute(text("DELETE FROM Calificaciones WHERE ID_Actividad = :act"), {"act": id_actividad})
            
            # 2. Borramos los incisos y luego las preguntas
            db.execute(text("DELETE FROM OpcionesPregunta WHERE ID_Pregunta IN (SELECT ID_Pregunta FROM PreguntasExamen WHERE ID_Actividad = :act)"), {"act": id_actividad})
            db.execute(text("DELETE FROM PreguntasExamen WHERE ID_Actividad = :act"), {"act": id_actividad})
            
            # 3. Finalmente, borramos la actividad por completo de la base de datos
            db.delete(act)
            db.commit()
            
            db.close()
            return redirect(url_for('ver_grupo', id_grupo=id_grupo))
            
    except Exception as e:
        db.rollback() # Si algo sale mal, deshacemos todo para evitar basura en la base de datos
        print(f"Error al eliminar actividad: {e}")
        
    db.close()
    return redirect(url_for('dashboard'))

# RUTA: Pantalla para editar un examen existente
@app.route('/actividad/<int:id_actividad>/editar')
def editar_examen(id_actividad):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return redirect(url_for('inicio'))
        
    db = SessionLocal()
    # Traemos el examen con todo y sus preguntas y opciones
    actividad = db.query(Actividad).options(joinedload(Actividad.grupo), joinedload(Actividad.preguntas).joinedload(PreguntaExamen.opciones)).filter_by(ID_Actividad=id_actividad).first()
    db.close()
    
    if not actividad:
        return redirect(url_for('dashboard'))
        
    return render_template('editar_examen.html', actividad=actividad)

# API: Guardar la actualización del examen
@app.route('/api/actividad/<int:id_actividad>/actualizar', methods=['POST'])
def actualizar_examen(id_actividad):
    if 'usuario_id' not in session or session.get('rol') not in ['Docente', 'Administrador']:
        return jsonify({"error": "No autorizado"}), 403
        
    db = SessionLocal()
    try:
        data = request.json
        act = db.query(Actividad).filter_by(ID_Actividad=id_actividad).first()
        
        # 1. Actualizamos los datos principales
        fecha_limite_str = data.get('fecha_limite')
        act.FechaLimite = datetime.strptime(fecha_limite_str, '%Y-%m-%dT%H:%M') if fecha_limite_str else None
        act.Titulo = data['titulo']
        act.TiempoMinutos = int(data['tiempo'])
        db.commit()
        
        # 2. Borramos las preguntas y opciones Viejas usando SQL puro
        db.execute(text("DELETE FROM OpcionesPregunta WHERE ID_Pregunta IN (SELECT ID_Pregunta FROM PreguntasExamen WHERE ID_Actividad = :act)"), {"act": id_actividad})
        db.execute(text("DELETE FROM PreguntasExamen WHERE ID_Actividad = :act"), {"act": id_actividad})
        db.commit()
        
        # 3. Insertamos las preguntas Nuevas (Para evitar el error de precisión HY104)
        for p_data in data['preguntas']:
            consulta_preg = text("""
                INSERT INTO PreguntasExamen (ID_Actividad, TextoPregunta)
                OUTPUT INSERTED.ID_Pregunta
                VALUES (:act, :txt)
            """)
            res_preg = db.execute(consulta_preg, {"act": id_actividad, "txt": p_data['texto']})
            id_preg = res_preg.fetchone()[0]
            
            for i, op_texto in enumerate(p_data['opciones']):
                es_correcta = 1 if i == int(p_data['correctaIndex']) else 0
                consulta_op = text("""
                    INSERT INTO OpcionesPregunta (ID_Pregunta, TextoOpcion, EsCorrecta)
                    VALUES (:preg, :txt, :corr)
                """)
                db.execute(consulta_op, {"preg": id_preg, "txt": op_texto, "corr": es_correcta})
                
        db.commit()
        db.close()
        return jsonify({"status": "success"})
        
    except Exception as e:
        db.rollback()
        db.close()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)