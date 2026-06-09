# Dashboard Educação Superior · Região de Campinas/SP

Este projeto é um **dashboard interativo** desenvolvido para análise da educação superior na região de Campinas e entorno, utilizando dados do Censo da Educação Superior (INEP) e MongoDB Atlas como banco de dados.

---

## 📋 Visão Geral

O dashboard oferece:
- **Indicadores gerais** da região (IES, cursos, vagas, alunos).
- **Análise por modalidade**, rede de ensino e categoria de custo.
- **Mapa interativo** da localização das instituições.
- **Comparativos** entre diferentes variáveis e métricas de atratividade.

---

## 🚀 Como Executar

### 1. Instalar dependências

Certifique-se de ter Python 3.8+ instalado.

```bash
pip install pandas pymongo plotly streamlit
```

### 2. Configurar MongoDB (secrets.toml)

Crie um arquivo `.streamlit/secrets.toml` com suas credenciais do MongoDB:

```toml
MONGO_URI = "mongodb+srv://<usuario>:<senha>@<cluster>.mongodb.net/?appName=AulaMongo"
```

### 3. Executar o Dashboard

```bash
streamlit run dashboard_educacao.py
```

---

## 📂 Estrutura do Projeto

```
.streamlit/
├── secrets.toml          # Credenciais do MongoDB
dashboard_educacao.py     # Aplicação Streamlit
README.md                 # Documentação do projeto
```

---

## 📊 Dataset

O projeto utiliza as seguintes coleções do MongoDB:

- `ies_info`: Informações sobre as Instituições de Ensino Superior.
- `docentes_indicadores`: Dados sobre corpo docente (doutorado, qualificação).
- `cursos_relacionados`: Relação de cursos oferecidos.
- `ies_perfil_estudante`: Perfil socioeconômico dos estudantes.

### Campos Relevantes:

| Tabela | Campos Chave |
|--------|--------------|
| `ies_info` | `nome`, `rede`, `categoria_mantenedora`, `municipio`, `estado`, `categoria_ies` |
| `docentes_indicadores` | `co_ies`, `perc_doutores`, `perc_qualificados` |
| `cursos_relacionados` | `co_ies`, `total_vagas`, `total_alunos`, `modalidade` |
| `ies_perfil_estudante` | `renda`, `escola_anterior`, `genero`, `idade` |

---

## 📊 KPIs Principais

### Métricas Gerais
- **Total de Instituições**
- **Total de Cursos**
- **Total de Vagas**
- **Total de Alunos**
- **Média de Alunos por Curso**
- **Média de Vagas por Curso**

### Análise por Modalidade
- Presencial vs. EAD
- Vagas por modalidade
- Alunos por modalidade

### Análise por Rede de Ensino
- Pública vs. Privada
- Distribuição de cursos por rede
- Alunos por rede

### Perfil do Estudante
- Distribuição por gênero
- Faixa etária
- Renda familiar
- Escola anterior

---

## 🎨 Paleta de Cores

- **Pública:** `#1D9E75` (verde)
- **Privada:** `#7F77DD` (roxo)
- **Accent:** `#EF9F27` (laranja)
- **Danger:** `#D85A30` (vermelho)

---

## 🛠️ Personalização

### Adicionar novas cidades

As coordenadas das cidades estão definidas no dicionário `COORDS`:
```python
COORDS = {
    "CAMPINAS": (-22.9056, -47.0608),
    "AMERICANA": (-22.7388, -47.3310),
    # ... adicione novas cidades aqui
}
```

### Filtros Interativos

O dashboard inclui filtros na barra lateral:
- Rede de Ensino (Pública/Privada)
- Categoria de IES
- Modalidade (Presencial/EAD)
- Faixa de Renda
- Faixa Etária
- Categoria de Custo

---

## 🐛 Solução de Problemas Comuns

### Erro: "MONGO_URI not found"

**Solução:** Verifique se o arquivo `.streamlit/secrets.toml` existe e contém a chave `MONGO_URI` correta.

### Erro: "Map key 'lat' or 'lon' not found"

**Solução:** Certifique-se de que as colunas `lat` e `lon` existem no DataFrame carregado. Se não existirem, adicione coordenadas ao dicionário `COORDS`.

### Erro: Gráficos não aparecem

**Solução:** Verifique se há conexão com o MongoDB e se os dados foram carregados corretamente. Execute `streamlit run dashboard_educacao.py --verbose` para ver logs detalhados.

---

## 🤝 Contribuindo

1. Crie uma branch para sua feature:
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```

2. Faça suas alterações

3. Envie seu pull request:
   ```bash
   git push origin feature/nova-funcionalidade
   ```

---

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos no âmbito da disciplina de Banco de Dados.

---

## 💡 Dicas Úteis

- Use `st.cache_data(ttl=300)` para cachear dados por 5 minutos (simula tempo real)
- Use `st.cache_resource` para cachear conexões ao banco de dados
- Use `st.sidebar` para criar painéis de controle
- Use `wide=True` para layout expandido

---

## 📚 Referências

- [Streamlit Documentation](https://docs.streamlit.io)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com)
- [Plotly Documentation](https://plotly.com/python)
- [Censo da Educação Superior (INEP)](https://www.gov.br/inep/)

---

## 📧 Contato

Para dúvidas ou sugestões, entre em contato com a equipe de desenvolvimento.