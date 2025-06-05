# seed_db.py
from sqlalchemy.orm import Session
from faker import Faker
from decimal import Decimal
from datetime import date, timedelta, time, datetime as dt_datetime # Renomeado para evitar conflito com a classe date
import random # Para escolhas aleatórias

# Importações do seu projeto
from app_models import Base, User, Escola, Responsavel, Aluno, Motorista, Van, ContratoServico, Pagamento, Rota, AlunosPorRota
from core_utils import engine, SessionLocal

from core_utils import get_password_hash
from contrato_servico_crud import proximo_mes as crud_proximo_mes


fake = Faker('pt_BR')

def seed_database():
    print("Iniciando o processo de seeding do banco de dados...")

    print("Recriando tabelas (drop_all, create_all)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tabelas recriadas.")

    db: Session = SessionLocal()

    try:
        # --- 1. CRIAR USUÁRIO FIXO PARA LOGIN ---
        print("Verificando/Criando usuário fixo 'lucas@gmail.com'...")
        fixed_user_email = "lucas@gmail.com"
        fixed_user_password = "lucas123"
        
        usuario_lucas = db.query(User).filter(User.email == fixed_user_email).first()
        
        if not usuario_lucas:
            hashed_password_fixo = get_password_hash(fixed_user_password)
            usuario_lucas = User(
                email=fixed_user_email,
                username="lucas_admin",
                hashed_password=hashed_password_fixo,
                nome_completo="Lucas (Admin do Sistema)",
                is_active=True,
                is_superuser=True 
            )
            db.add(usuario_lucas)
            db.commit()
            db.refresh(usuario_lucas)
            print(f"Usuário fixo '{usuario_lucas.email}' criado com ID: {usuario_lucas.id_user}.")
        else:
            print(f"Usuário fixo '{usuario_lucas.email}' já existe com ID: {usuario_lucas.id_user}.")
        
        proprietario_id = usuario_lucas.id_user # Todos os dados pertencerão a este usuário

        # --- Dados para o Operador Lucas ---
        print(f"\n--- Populando dados para o Operador: {usuario_lucas.email} (ID: {proprietario_id}) ---")

        # Criar Escolas
        escolas_criadas = []
        num_escolas = 5
        print(f"Criando {num_escolas} escolas...")
        for j in range(num_escolas):
            nome_esc = fake.unique.company() + " Escola Mockup"
            escola = Escola(
                nome_escola=nome_esc[:99],
                cnpj=fake.unique.cnpj(),
                endereco_completo=fake.address(),
                telefone_escola=fake.phone_number(),
                nome_contato_escola=fake.name(),
                email_contato_escola=fake.unique.email(),
                id_proprietario_user=proprietario_id
            )
            db.add(escola)
            escolas_criadas.append(escola)
        db.commit()
        for esc in escolas_criadas: db.refresh(esc)
        print(f"  {len(escolas_criadas)} escolas criadas.")
        if not escolas_criadas: return print("  Nenhuma escola criada, seeding interrompido.")


        # Criar Responsáveis
        responsaveis_criados = []
        num_responsaveis = 30
        print(f"Criando {num_responsaveis} responsáveis...")
        for j in range(num_responsaveis):
            responsavel = Responsavel(
                nome_completo=fake.name(),
                cpf=fake.unique.cpf(),
                email=fake.unique.email(),
                telefone_principal=fake.phone_number(),
                endereco_completo=fake.address(),
                id_proprietario_user=proprietario_id
            )
            db.add(responsavel)
            responsaveis_criados.append(responsavel)
        db.commit()
        for resp in responsaveis_criados: db.refresh(resp)
        print(f"  {len(responsaveis_criados)} responsáveis criados.")
        if not responsaveis_criados: return print("  Nenhum responsável criado, seeding interrompido.")

        # Criar Alunos
        alunos_criados = []
        num_alunos = 60
        print(f"Criando {num_alunos} alunos...")
        for j in range(num_alunos):
            aluno = Aluno(
                nome_completo_aluno=fake.name(),
                data_nascimento=fake.date_of_birth(minimum_age=5, maximum_age=15),
                id_responsavel_principal=random.choice(responsaveis_criados).id_responsavel,
                id_responsavel_secundario=random.choice(responsaveis_criados).id_responsavel if fake.boolean(chance_of_getting_true=25) else None,
                id_escola=random.choice(escolas_criadas).id_escola,
                endereco_embarque_predeterminado=fake.street_address(),
                periodo_escolar=random.choice(["Manhã", "Tarde", "Integral"]),
                turma_serie=f"{random.randint(1,9)}º {random.choice(['A','B','C'])}",
                id_proprietario_user=proprietario_id
            )
            db.add(aluno)
            alunos_criados.append(aluno)
        db.commit()
        for al in alunos_criados: db.refresh(al)
        print(f"  {len(alunos_criados)} alunos criados.")
        if not alunos_criados: return print("  Nenhum aluno criado, seeding interrompido.")

        # Criar Motoristas
        motoristas_criados = []
        num_motoristas = 7
        print(f"Criando {num_motoristas} motoristas...")
        for j in range(num_motoristas):
            motorista = Motorista(
                nome_completo=fake.name(),
                cpf=fake.unique.cpf(),
                cnh_numero=str(fake.unique.random_number(digits=9, fix_len=True)),
                cnh_categoria=random.choice(["B", "D", "E"]),
                cnh_validade=date.today() + timedelta(days=random.randint(30, 365*3)),
                telefone=fake.phone_number(),
                email=fake.unique.email(),
                id_proprietario_user=proprietario_id
            )
            db.add(motorista)
            motoristas_criados.append(motorista)
        db.commit()
        for mot in motoristas_criados: db.refresh(mot)
        print(f"  {len(motoristas_criados)} motoristas criados.")
        if not motoristas_criados: return print("  Nenhum motorista criado, seeding interrompido.")

        # Criar Vans
        vans_criadas = []
        num_vans = 10
        print(f"Criando {num_vans} vans...")
        for j in range(num_vans):
            van = Van(
                placa=fake.unique.license_plate(),
                modelo_veiculo=random.choice(["Sprinter", "Ducato", "Transit", "Master", "Boxer"]),
                marca_veiculo=random.choice(["Mercedes", "Fiat", "Ford", "Renault", "Peugeot"]),
                ano_fabricacao=random.randint(2015, date.today().year),
                capacidade_passageiros=random.randint(10, 20),
                id_motorista_padrao=random.choice(motoristas_criados).id_motorista if motoristas_criados and fake.boolean(chance_of_getting_true=70) else None,
                status_van="Ativa",
                id_proprietario_user=proprietario_id
            )
            db.add(van)
            vans_criadas.append(van)
        db.commit()
        for v in vans_criadas: db.refresh(v)
        print(f"  {len(vans_criadas)} vans criadas.")
        if not vans_criadas: return print("  Nenhuma van criada, seeding interrompido.")

        # Criar Contratos e Pagamentos
        num_contratos = min(len(alunos_criados), 40) # Até 40 contratos
        print(f"Criando {num_contratos} contratos e seus pagamentos...")
        contratos_criados = []
        alunos_com_contrato = random.sample(alunos_criados, num_contratos)

        for aluno_contrato in alunos_com_contrato:
            data_inicio_c = fake.date_between_dates(date_start=date(date.today().year -1, 1, 1), date_end=date.today())
            # 70% chance de ter data_fim_contrato, senão pagamentos até fim do ano de início
            if fake.boolean(chance_of_getting_true=70):
                data_fim_c = data_inicio_c + timedelta(days=random.randint(90, 400))
            else:
                data_fim_c = None 

            contrato = ContratoServico(
                id_aluno=aluno_contrato.id_aluno,
                id_responsavel_financeiro=aluno_contrato.id_responsavel_principal, # Simplificando
                data_inicio_contrato=data_inicio_c,
                data_fim_contrato=data_fim_c,
                valor_mensal=Decimal(str(random.randint(150, 450)) + ".50"),
                dia_vencimento_mensalidade=random.choice([5, 10, 15, 20, 25]),
                tipo_servico_contratado=fake.bs(),
                id_proprietario_user=proprietario_id
            )
            
            pagamentos_para_este_contrato = []
            data_fim_efetiva_para_pagamentos_seed: date
            if contrato.data_fim_contrato is None:
                ano_inicio_seed = contrato.data_inicio_contrato.year
                data_fim_efetiva_para_pagamentos_seed = date(ano_inicio_seed, 12, 31)
            else:
                data_fim_efetiva_para_pagamentos_seed = contrato.data_fim_contrato

            mes_iterador_seed = date(contrato.data_inicio_contrato.year, contrato.data_inicio_contrato.month, 1)
            hoje_seed = date.today()

            while mes_iterador_seed <= data_fim_efetiva_para_pagamentos_seed:
                ano_ref = mes_iterador_seed.year
                mes_ref_int = mes_iterador_seed.month
                try:
                    data_venc = date(ano_ref, mes_ref_int, contrato.dia_vencimento_mensalidade)
                except ValueError:
                    if mes_ref_int == 12: ultimo_dia_mes = date(ano_ref, mes_ref_int, 31)
                    else: ultimo_dia_mes = date(ano_ref, mes_ref_int + 1, 1) - timedelta(days=1)
                    data_venc = ultimo_dia_mes

                status_inicial_pagamento = "Pendente"
                if data_venc < hoje_seed: status_inicial_pagamento = "Atrasado"

                pagamento_obj = Pagamento(
                    mes_referencia=f"{ano_ref:04d}-{mes_ref_int:02d}",
                    ano_referencia=ano_ref, data_vencimento=data_venc,
                    valor_nominal=contrato.valor_mensal,
                    status_pagamento=status_inicial_pagamento,
                )
                pagamentos_para_este_contrato.append(pagamento_obj)
                ano_ref_prox, mes_ref_int_prox = crud_proximo_mes(ano_ref, mes_ref_int)
                mes_iterador_seed = date(ano_ref_prox, mes_ref_int_prox, 1)
            
            contrato.pagamentos = pagamentos_para_este_contrato
            db.add(contrato)
            contratos_criados.append(contrato)
        db.commit()
        for c in contratos_criados: db.refresh(c)
        print(f"  {len(contratos_criados)} contratos e seus respectivos pagamentos criados.")

        # Criar Rotas
        rotas_criadas = []
        num_rotas = min(len(vans_criadas), len(motoristas_criados), len(escolas_criadas), 4) # No máximo 4 rotas
        print(f"Criando {num_rotas} rotas...")
        for j in range(num_rotas):
            rota = Rota(
                nome_rota=f"Rota {fake.street_name()} {random.choice(['Manhã', 'Tarde'])}",
                id_van_designada=vans_criadas[j % len(vans_criadas)].id_van,
                id_motorista_escalado=motoristas_criados[j % len(motoristas_criados)].id_motorista,
                id_escola_atendida=escolas_criadas[j % len(escolas_criadas)].id_escola,
                tipo_rota=random.choice(["Ida Manhã", "Volta Tarde", "Completa Manhã", "Completa Tarde"]),
                horario_partida_estimado=time(random.randint(6,7), random.choice([0,15,30,45])),
                horario_chegada_estimado_escola=time(random.randint(7,8), random.choice([0,15,30,45])),
                id_proprietario_user=proprietario_id
            )
            db.add(rota)
            rotas_criadas.append(rota)
        db.commit()
        for r in rotas_criadas: db.refresh(r)
        print(f"  {len(rotas_criadas)} rotas criadas.")

        # Alocar Alunos em Rotas
        if rotas_criadas and alunos_criados:
            print(f"Alocando alunos em rotas...")
            alunos_alocados_count = 0
            for aluno_item in alunos_criados:
                if fake.boolean(chance_of_getting_true=60): # 60% de chance de alocar o aluno
                    rota_escolhida = random.choice(rotas_criadas)
                    # Verifica se o aluno já está ativo nessa rota
                    assoc_existente = db.query(AlunosPorRota).filter(
                        AlunosPorRota.id_aluno == aluno_item.id_aluno,
                        AlunosPorRota.id_rota == rota_escolhida.id_rota,
                        AlunosPorRota.data_fim_na_rota == None # noqa E711
                    ).first()
                    if not assoc_existente:
                        alocacao = AlunosPorRota(
                            id_aluno=aluno_item.id_aluno,
                            id_rota=rota_escolhida.id_rota,
                            ponto_embarque_especifico=fake.street_address() if fake.boolean(chance_of_getting_true=20) else aluno_item.endereco_embarque_predeterminado,
                            status_aluno_na_rota="Ativo",
                            data_inicio_na_rota=date.today() - timedelta(days=random.randint(0,30))
                        )
                        db.add(alocacao)
                        alunos_alocados_count +=1
            if alunos_alocados_count > 0:
                db.commit()
            print(f"  {alunos_alocados_count} alocações de alunos em rotas realizadas.")


        print("\nSeeding do banco de dados concluído com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"Erro durante o seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    confirm_text = "Este script pode REPOPULAR seu banco de dados."
    try:
        with open(__file__, 'r') as f:
            content = f.read()
            if "Base.metadata.drop_all(bind=engine)" in content and \
               not "# Base.metadata.drop_all(bind=engine)" in content:
                confirm_text = "Este script irá APAGAR e REPOPULAR seu banco de dados."
    except Exception:
        pass # Mantém o texto padrão se não conseguir ler o arquivo

    print(f"\nAVISO: {confirm_text}")
    confirm = input("Tem certeza que deseja continuar? (s/N): ")
    if confirm.lower() == 's':
        seed_database()
    else:
        print("Operação de seeding cancelada.")