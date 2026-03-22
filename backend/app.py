import os
from datetime import datetime
import pandas as pd
import io
from flask import Flask, request, session, send_file, send_from_directory
from flask_cors import CORS
from sqlalchemy import func, desc
from .models import db, Prospecto, Seguimiento, Usuario, EscuelaProcedencia, OfertaAcademica, MetaVendedor, Carrera, Periodo, Turno
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_app():
    app = Flask(__name__, static_folder='static')
    
    # Use absolute path for database
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    db_path = os.path.join(instance_path, 'crm.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-super-secret')
    
    CORS(app)
    db.init_app(app)
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_proxy(path):
        return send_from_directory(app.static_folder, path)
    
    with app.app_context():
        db.create_all()
    
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.json
        u = Usuario.query.filter_by(email=data.get('email')).first()
        if u and u.check_password(data.get('password')):
            session['user_id'] = u.id_usuario
            session['rol'] = u.rol
            return u.to_dict()
        return {'error': 'Credenciales inválidas'}, 401

    @app.route('/api/logout', methods=['POST'])
    def logout():
        session.clear()
        return {'message': 'Logged out'}
        
    @app.route('/api/me', methods=['GET'])
    def me():
        if 'user_id' in session:
            u = Usuario.query.get(session['user_id'])
            if u:
                return u.to_dict()
        return {'error': 'No autorizado'}, 401
    
    @app.route('/api/prospectos', methods=['GET'])
    def get_prospectos():
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        query = Prospecto.query.filter(Prospecto.fase_crm != 'PERDIDO')
        
        # If per_page is -1, return all (for compatibility or specific needs)
        if per_page == -1:
            prospectos = query.all()
            return {
                'prospectos': [p.to_dict() for p in prospectos],
                'total': len(prospectos),
                'pages': 1,
                'current_page': 1
            }
            
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            'prospectos': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }

    @app.route('/api/prospectos', methods=['POST'])
    def create_prospecto():
        data = request.json
        
        fecha_captura = None
        if data.get('fecha_captura'):
            try:
                fecha_captura = datetime.strptime(data['fecha_captura'], '%Y-%m-%d').date()
            except:
                pass

        # Auto-assign if not provided and user is logged in
        vendedor_id = data.get('id_vendedor_asignado')
        if not vendedor_id and 'user_id' in session:
            vendedor_id = session['user_id']

        nuevo = Prospecto(
            nombre=data['nombre'],
            apellido_paterno=data['apellido_paterno'],
            apellido_materno=data.get('apellido_materno'),
            sexo=data.get('sexo'),
            fecha_captura=fecha_captura,
            turno=data.get('turno'),
            email=data.get('email'),
            telefono=data.get('telefono'),
            id_escuela=data.get('id_escuela'),
            semestre=data.get('semestre'),
            promedio=data.get('promedio'),
            carrera_interes=data.get('carrera_interes'),
            origen_prospecto=data.get('origen_prospecto'),
            id_vendedor_asignado=vendedor_id
        )
        db.session.add(nuevo)
        db.session.commit()
        return nuevo.to_dict(), 201

    @app.route('/api/escuelas', methods=['GET'])
    def get_escuelas():
        escuelas = EscuelaProcedencia.query.all()
        return {'escuelas': [e.to_dict() for e in escuelas]}

    @app.route('/api/escuelas', methods=['POST'])
    def create_escuela():
        data = request.json
        nueva = EscuelaProcedencia(nombre_escuela=data['nombre_escuela'])
        db.session.add(nueva)
        db.session.commit()
        return nueva.to_dict(), 201

    @app.route('/api/prospectos/<int:id_prospecto>/fase', methods=['PATCH'])
    def update_fase(id_prospecto):
        from flask import request
        data = request.json
        p = Prospecto.query.get_or_404(id_prospecto)
        p.fase_crm = data['fase_crm']
        if data['fase_crm'] == 'INSCRITO' and 'id_oferta_inscripcion' in data:
            p.id_oferta_inscripcion = data['id_oferta_inscripcion']
        db.session.commit()
        return p.to_dict()

    @app.route('/api/prospectos/<int:id_prospecto>/perdido', methods=['PATCH'])
    def update_perdido(id_prospecto):
        data = request.json
        p = Prospecto.query.get_or_404(id_prospecto)
        p.fase_crm = 'PERDIDO'
        p.razon_perdido = data.get('razon_perdido')
        db.session.commit()
        return p.to_dict()

    @app.route('/api/prospectos/<int:id_prospecto>/seguimiento', methods=['GET'])
    def get_seguimiento(id_prospecto):
        seguimientos = Seguimiento.query.filter_by(id_prospecto=id_prospecto).all()
        return {'seguimientos': [s.to_dict() for s in seguimientos]}

    @app.route('/api/prospectos/<int:id_prospecto>/seguimiento', methods=['POST'])
    def create_seguimiento(id_prospecto):
        data = request.json
        nuevo = Seguimiento(
            id_prospecto=id_prospecto,
            tipo_contacto=data['tipo_contacto'],
            comentarios=data['comentarios'],
            proxima_accion_fecha=data.get('proxima_accion_fecha'),
            proxima_accion_nota=data.get('proxima_accion_nota')
        )
        db.session.add(nuevo)
        db.session.commit()
        return nuevo.to_dict(), 201


    @app.route('/api/prospectos/<int:id_prospecto>', methods=['PUT'])
    def update_prospecto(id_prospecto):
        data = request.json
        p = Prospecto.query.get_or_404(id_prospecto)
        
        p.nombre = data.get('nombre', p.nombre)
        p.apellido_paterno = data.get('apellido_paterno', p.apellido_paterno)
        p.apellido_materno = data.get('apellido_materno', p.apellido_materno)
        p.sexo = data.get('sexo', p.sexo)
        
        if 'fecha_captura' in data and data['fecha_captura']:
            try:
                p.fecha_captura = datetime.strptime(data['fecha_captura'], '%Y-%m-%d').date()
            except:
                pass
        
        p.turno = data.get('turno', p.turno)
        p.email = data.get('email', p.email)
        p.telefono = data.get('telefono', p.telefono)
        p.id_escuela = data.get('id_escuela', p.id_escuela)
        p.semestre = data.get('semestre', p.semestre)
        p.promedio = data.get('promedio', p.promedio)
        p.carrera_interes = data.get('carrera_interes', p.carrera_interes)
        p.origen_prospecto = data.get('origen_prospecto', p.origen_prospecto)
        
        db.session.commit()
        return p.to_dict()

    @app.route('/api/admin/dashboard', methods=['GET'])
    def admin_dashboard():
        stats = db.session.query(Prospecto.fase_crm, func.count(Prospecto.id_prospecto)).group_by(Prospecto.fase_crm).all()
        return {'stats': dict(stats)}

    @app.route('/api/admin/template/download', methods=['GET'])
    def download_template():
        cols = ['nombre', 'apellido_paterno', 'apellido_materno', 'email', 'telefono', 'sexo', 'turno', 'semestre', 'promedio', 'carrera_interes', 'origen_prospecto', 'escuela']
        example_data = [
            ['Juan', 'Perez', 'Lopez', 'juan@example.com', '9981234567', 'M', 'MATUTINO', 6, 8.5, 'Derecho', 'WEB', 'Bachillerato Central'],
            ['Maria', 'Garcia', '', 'maria@example.com', '9987654321', 'F', 'VESPERTINO', 5, 9.0, 'Psicología', 'SALONEO', 'Preparatoria Norte']
        ]
        df = pd.DataFrame(example_data, columns=cols)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Prospectos')
        output.seek(0)
        return send_file(output, download_name='plantilla_prospectos.xlsx', as_attachment=True)

    @app.route('/api/admin/prospectos/upload', methods=['POST'])
    def bulk_upload_prospectos():
        
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            return {'error': 'No autorizado'}, 403
            
        if 'file' not in request.files:
            return {'error': 'No hay archivo'}, 400
            
        file = request.files['file']
        if file.filename == '':
            return {'error': 'Archivo sin nombre'}, 400
            
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
                
            imported_count = 0
            errors = []
            vendedor_id = session.get('user_id')
            
            for idx, row in df.iterrows():
                nombre = str(row.get('nombre', '')).strip()
                apellido = str(row.get('apellido_paterno', '')).strip()
                
                if not nombre or not apellido or nombre == 'nan' or apellido == 'nan':
                    errors.append({'fila': idx + 2, 'error': 'Nombre o Apellido incompleto'})
                    continue
                
                email = str(row.get('email', '')).strip() if not pd.isna(row.get('email')) else None
                telefono = str(row.get('telefono', '')).strip() if not pd.isna(row.get('telefono')) else None
                
                # Handle Escuela
                escuela_nombre = str(row.get('escuela', '')).strip()
                id_escuela = None
                if escuela_nombre and escuela_nombre != 'nan':
                    esc = EscuelaProcedencia.query.filter_by(nombre_escuela=escuela_nombre).first()
                    if not esc:
                        esc = EscuelaProcedencia(nombre_escuela=escuela_nombre)
                        db.session.add(esc)
                        db.session.flush()
                    id_escuela = esc.id_escuela

                # Check for duplicates
                duplicate = None
                if email and email != 'nan':
                    duplicate = Prospecto.query.filter_by(email=email).first()
                    if duplicate:
                        errors.append({'fila': idx + 2, 'nombre': f"{nombre} {apellido}", 'motivo': f'Email duplicado (Estatus: {duplicate.fase_crm})'})
                        continue
                        
                if telefono and telefono != 'nan':
                    duplicate = Prospecto.query.filter_by(telefono=telefono).first()
                    if duplicate:
                        errors.append({'fila': idx + 2, 'nombre': f"{nombre} {apellido}", 'motivo': f'Teléfono duplicado (Estatus: {duplicate.fase_crm})'})
                        continue
                
                nuevo = Prospecto(
                    nombre=nombre,
                    apellido_paterno=apellido,
                    apellido_materno=str(row.get('apellido_materno', '')) if not pd.isna(row.get('apellido_materno')) and str(row.get('apellido_materno')) != 'nan' else None,
                    email=email if email != 'nan' else None,
                    telefono=telefono if telefono != 'nan' else None,
                    sexo=str(row.get('sexo', 'M')),
                    turno=str(row.get('turno', 'MATUTINO')),
                    semestre=int(row['semestre']) if not pd.isna(row.get('semestre')) else None,
                    promedio=float(row['promedio']) if not pd.isna(row.get('promedio')) else None,
                    carrera_interes=str(row.get('carrera_interes', '')) if not pd.isna(row.get('carrera_interes')) and str(row.get('carrera_interes')) != 'nan' else None,
                    origen_prospecto=str(row.get('origen_prospecto', 'WEB')),
                    id_escuela=id_escuela,
                    id_vendedor_asignado=None # Bulk upload starts as unassigned
                )
                db.session.add(nuevo)
                imported_count += 1
                
            db.session.commit()
            return {'imported': imported_count, 'errors': errors}, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

    @app.route('/api/admin/prospectos/repartir-equitativo', methods=['POST'])
    def repartir_equitativo():
        vendedores = Usuario.query.filter_by(rol='VENDEDOR').all()
        if not vendedores:
            return {'error': 'No hay vendedores (VENDEDOR) registrados para repartir.'}, 400
            
        sin_asignar = Prospecto.query.filter_by(id_vendedor_asignado=None).all()
        if not sin_asignar:
            return {'message': 'No hay prospectos sin asignar.'}, 200
            
        num_v = len(vendedores)
        for i, p in enumerate(sin_asignar):
            p.id_vendedor_asignado = vendedores[i % num_v].id_usuario
            
        db.session.commit()
        return {'message': f'Se han repartido {len(sin_asignar)} prospectos equitativamente entre {num_v} ejecutivos.'}

    @app.route('/api/admin/prospectos/<int:id_prospecto>/vendedor', methods=['PATCH'])
    def reassign_prospecto(id_prospecto):
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            return {'error': 'No autorizado'}, 403
            
        data = request.json
        p = Prospecto.query.get_or_404(id_prospecto)
        p.id_vendedor_asignado = data.get('id_vendedor_asignado')
        db.session.commit()
        return p.to_dict()

    @app.route('/api/admin/finanzas', methods=['GET'])
    def get_finanzas():
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            return {'error': 'No autorizado'}, 403
            
        # Optimization: use a single query with outer join and count
        results = db.session.query(
            OfertaAcademica,
            func.count(Prospecto.id_prospecto).label('num_inscritos')
        ).outerjoin(
            Prospecto, 
            (Prospecto.id_oferta_inscripcion == OfertaAcademica.id_oferta) & (Prospecto.fase_crm == 'INSCRITO')
        ).group_by(OfertaAcademica.id_oferta).all()
        
        finanzas = []
        for oferta, inscritos in results:
            data = oferta.to_dict()
            data['num_inscritos'] = inscritos
            data['monto_esperado'] = inscritos * oferta.costo
            finanzas.append(data)
            
        return {'finanzas': finanzas}

    @app.route('/api/admin/kpi/metas', methods=['GET', 'POST'])
    def handle_metas():
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            return {'error': 'No autorizado'}, 403
            
        if request.method == 'GET':
            mes = request.args.get('mes')
            query = MetaVendedor.query
            if mes:
                query = query.filter_by(periodo_mes=mes)
            metas = query.all()
            return {'metas': [m.to_dict() for m in metas]}
            
        if request.method == 'POST':
            data = request.json
            meta = MetaVendedor.query.filter_by(id_usuario=data['id_usuario'], periodo_mes=data['periodo_mes']).first()
            if meta:
                meta.meta_contactos = data.get('meta_contactos', meta.meta_contactos)
                meta.meta_inscritos = data.get('meta_inscritos', meta.meta_inscritos)
            else:
                meta = MetaVendedor(
                    id_usuario=data['id_usuario'],
                    periodo_mes=data['periodo_mes'],
                    meta_contactos=data.get('meta_contactos', 0),
                    meta_inscritos=data.get('meta_inscritos', 0)
                )
                db.session.add(meta)
            db.session.commit()
            return meta.to_dict(), 201

    @app.route('/api/admin/kpi/reporte', methods=['GET'])
    def get_kpi_reporte():
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role not in ['ADMIN', 'SUPERADMIN']:
            return {'error': 'No autorizado'}, 403
            
        mes = request.args.get('mes')
        if not mes:
            return {'error': 'Parametro mes es requerido, formato YYYY-MM'}, 400
            
        vendedores = Usuario.query.filter_by(rol='VENDEDOR').all()
        metas = {m.id_usuario: m for m in MetaVendedor.query.filter_by(periodo_mes=mes).all()}
        
        # Optimization: Aggregate Seguimientos (contactos)
        seguimientos_stats = dict(db.session.query(
            Prospecto.id_vendedor_asignado,
            func.count(Seguimiento.id_seguimiento)
        ).join(Seguimiento).filter(
            func.strftime('%Y-%m', Seguimiento.fecha_creacion) == mes
        ).group_by(Prospecto.id_vendedor_asignado).all())
        
        # Optimization: Aggregate Inscritos
        inscritos_stats = dict(db.session.query(
            Prospecto.id_vendedor_asignado,
            func.count(Prospecto.id_prospecto)
        ).filter(
            Prospecto.fase_crm == 'INSCRITO',
            func.strftime('%Y-%m', Prospecto.fecha_registro) == mes
        ).group_by(Prospecto.id_vendedor_asignado).all())
        
        reporte = []
        for v in vendedores:
            meta = metas.get(v.id_usuario)
            reporte.append({
                'id_usuario': v.id_usuario,
                'vendedor_nombre': v.nombre_completo,
                'mes': mes,
                'meta_contactos': meta.meta_contactos if meta else 0,
                'real_contactos': seguimientos_stats.get(v.id_usuario, 0),
                'meta_inscritos': meta.meta_inscritos if meta else 0,
                'real_inscritos': inscritos_stats.get(v.id_usuario, 0)
            })
            
        return {'reporte': reporte}

    @app.route('/api/admin/prospectos/<fase>', methods=['GET'])
    def get_prospectos_por_fase(fase):
        prospectos = Prospecto.query.filter_by(fase_crm=fase).all()
        return {'prospectos': [p.to_dict() for p in prospectos]}

    # Oferta Academica Management Endpoints
    @app.route('/api/admin/carreras', methods=['GET'])
    def get_carreras():
        carreras = Carrera.query.all()
        return {'carreras': [c.to_dict() for c in carreras]}

    @app.route('/api/admin/carreras', methods=['POST'])
    def create_carrera():
        data = request.json
        nueva = Carrera(nombre=data['nombre'])
        db.session.add(nueva)
        db.session.commit()
        return nueva.to_dict(), 201

    @app.route('/api/admin/periodos', methods=['GET'])
    def get_periodos():
        periodos = Periodo.query.all()
        return {'periodos': [p.to_dict() for p in periodos]}

    @app.route('/api/admin/periodos', methods=['POST'])
    def create_periodo():
        data = request.json
        nuevo = Periodo(nombre=data['nombre'])
        db.session.add(nuevo)
        db.session.commit()
        return nuevo.to_dict(), 201

    @app.route('/api/admin/turnos', methods=['GET'])
    def get_turnos():
        turnos = Turno.query.all()
        return {'turnos': [t.to_dict() for t in turnos]}

    @app.route('/api/admin/turnos', methods=['POST'])
    def create_turno():
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role != 'SUPERADMIN':
            return {'error': 'Solo el superadministrador puede agregar turnos'}, 403
            
        data = request.json
        nuevo = Turno(nombre=data['nombre'])
        db.session.add(nuevo)
        db.session.commit()
        return nuevo.to_dict(), 201

    @app.route('/api/admin/ofertas', methods=['GET'])
    def get_ofertas():
        ofertas = OfertaAcademica.query.all()
        return {'ofertas': [o.to_dict() for o in ofertas]}

    @app.route('/api/admin/ofertas', methods=['POST'])
    def create_oferta():
        data = request.json
        
        if data['id_carrera'] == 'ALL':
            carreras = Carrera.query.all()
            nuevas = []
            for c in carreras:
                nueva = OfertaAcademica(
                    id_carrera=c.id_carrera,
                    id_periodo=data['id_periodo'],
                    id_turno=data.get('id_turno', 1),
                    costo=data['costo']
                )
                db.session.add(nueva)
                nuevas.append(nueva)
            db.session.commit()
            return {'message': f'{len(nuevas)} ofertas creadas'}, 201
        else:
            nueva = OfertaAcademica(
                id_carrera=data['id_carrera'],
                id_periodo=data['id_periodo'],
                id_turno=data.get('id_turno', 1),
                costo=data['costo']
            )
            db.session.add(nueva)
            db.session.commit()
            return nueva.to_dict(), 201

    @app.route('/api/admin/ofertas/<int:id_oferta>', methods=['PUT', 'DELETE'])
    def modify_oferta(id_oferta):
        user_role = request.headers.get('X-Role', 'VENDEDOR')
        if user_role != 'SUPERADMIN':
            return {'error': 'Solo el superadministrador puede modificar o eliminar ofertas'}, 403
            
        oferta = OfertaAcademica.query.get_or_404(id_oferta)
        
        if request.method == 'DELETE':
            db.session.delete(oferta)
            db.session.commit()
            return {'message': 'Oferta eliminada'}
            
        elif request.method == 'PUT':
            data = request.json
            if 'costo' in data:
                oferta.costo = data['costo']
            if 'id_carrera' in data:
                oferta.id_carrera = data['id_carrera']
            if 'id_periodo' in data:
                oferta.id_periodo = data['id_periodo']
            if 'id_turno' in data:
                oferta.id_turno = data['id_turno']
            db.session.commit()
            return oferta.to_dict()

    # User Management Endpoints
    @app.route('/api/admin/usuarios', methods=['GET'])
    def get_usuarios():
        usuarios = Usuario.query.all()
        return {'usuarios': [u.to_dict() for u in usuarios]}

    @app.route('/api/admin/usuarios', methods=['POST'])
    def create_usuario():
        data = request.json
        nuevo = Usuario(
            nombre_completo=data['nombre_completo'],
            email=data.get('email'),
            rol=data.get('rol', 'VENDEDOR')
        )
        if data.get('password'):
            nuevo.set_password(data.get('password'))
        db.session.add(nuevo)
        db.session.commit()
        return nuevo.to_dict(), 201

    @app.route('/api/admin/usuarios/<int:id_usuario>', methods=['PUT'])
    def update_usuario(id_usuario):
        data = request.json
        u = Usuario.query.get_or_404(id_usuario)
        u.nombre_completo = data.get('nombre_completo', u.nombre_completo)
        u.email = data.get('email', u.email)
        u.rol = data.get('rol', u.rol)
        if data.get('password'):
            u.set_password(data.get('password'))
        db.session.commit()
        return u.to_dict()

    @app.route('/api/admin/usuarios/<int:id_usuario>', methods=['DELETE'])
    def delete_usuario(id_usuario):
        u = Usuario.query.get_or_404(id_usuario)
        db.session.delete(u)
        db.session.commit()
        return {'message': 'Usuario eliminado'}

    @app.route('/api/reportes/prospectos', methods=['GET'])
    def get_reporte_prospectos():
        
        fase = request.args.get('fase')
        id_vendedor = request.args.get('id_vendedor')
        id_escuela = request.args.get('id_escuela')
        promedio_min = request.args.get('promedio_min')
        promedio_max = request.args.get('promedio_max')
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        query = Prospecto.query
        
        if fase:
            query = query.filter(Prospecto.fase_crm == fase)
        if id_vendedor:
            query = query.filter(Prospecto.id_vendedor_asignado == id_vendedor)
        if id_escuela:
            query = query.filter(Prospecto.id_escuela == id_escuela)
        if promedio_min:
            query = query.filter(Prospecto.promedio >= float(promedio_min))
        if promedio_max:
            query = query.filter(Prospecto.promedio <= float(promedio_max))
            
        if fecha_inicio or fecha_fin:
            subq = db.session.query(
                Seguimiento.id_prospecto,
                func.max(Seguimiento.fecha_creacion).label('max_fecha')
            ).group_by(Seguimiento.id_prospecto).subquery()
            
            query = query.join(subq, Prospecto.id_prospecto == subq.c.id_prospecto)
            
            if fecha_inicio:
                query = query.filter(func.date(subq.c.max_fecha) >= fecha_inicio)
            if fecha_fin:
                query = query.filter(func.date(subq.c.max_fecha) <= fecha_fin)

        prospectos = query.all()
        return {'prospectos': [p.to_dict() for p in prospectos]}

    @app.route('/api/reportes/prospectos/excel', methods=['GET'])
    def export_reporte_excel():
        
        response = get_reporte_prospectos()
        data = response.get('prospectos', [])
        
        df = pd.DataFrame(data)
        if not df.empty:
            cols_to_keep = ['id_prospecto', 'nombre_solo', 'apellido_paterno', 'apellido_materno', 'fase_crm', 'escuela', 'carrera_interes', 'promedio', 'vendedor_nombre', 'ultimo_seguimiento', 'telefono', 'email']
            existing_cols = [c for c in cols_to_keep if c in df.columns]
            df = df[existing_cols]
            df.columns = ['ID', 'Nombre', 'Apellido Pat.', 'Apellido Mat.', 'Fase', 'Escuela', 'Carrera Interés', 'Promedio', 'Vendedor', 'Último Seg.', 'Teléfono', 'Email']
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Prospectos')
        
        output.seek(0)
        return send_file(output, download_name='reporte_prospectos.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    @app.route('/api/reportes/prospectos/pdf', methods=['GET'])
    def export_reporte_pdf():
        
        response = get_reporte_prospectos()
        data = response.get('prospectos', [])
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(letter))
        elements = []
        
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Reporte de Prospectos", styles['Title']))
        elements.append(Spacer(1, 12))
        
        table_data = [['ID', 'Nombre', 'Apellido', 'Fase', 'Escuela', 'Carrera', 'Promedio', 'Vendedor', 'Último Seg.']]
        
        for p in data:
            def trunc(s, l=15):
                return (str(s)[:l] + '...') if s and len(str(s)) > l else str(s or '')
                
            row = [
                str(p.get('id_prospecto', '')),
                trunc(p.get('nombre_solo', '')),
                trunc(p.get('apellido_paterno', '')),
                trunc(p.get('fase_crm', '')),
                trunc(p.get('escuela', ''), 20),
                trunc(p.get('carrera_interes', '')),
                str(p.get('promedio') or ''),
                trunc(p.get('vendedor_nombre', '')),
                trunc(p.get('ultimo_seguimiento', '')[:10] if p.get('ultimo_seguimiento') else '')
            ]
            table_data.append(row)
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.Color(0.2, 0.4, 0.6)),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        
        elements.append(t)
        doc.build(elements)
        
        output.seek(0)
        return send_file(output, download_name='reporte_prospectos.pdf', as_attachment=True, mimetype='application/pdf')

    return app

if __name__ == '__main__':
    app = create_app()
    # Check if in production
    is_prod = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('PRODUCTION') == 'True'
    app.run(debug=not is_prod, host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
