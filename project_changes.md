**Alterações Programadas - Projeto \'Advocacia e IA\'**

1\. Permitir a inclusão do número do processo após a abertura do caso,
quando se tratar de um processo inicial. O número de 20 dígitos de um
processo judicial é gerado quando a petição inicial é protocolada e o
processo é registrado na distribuição do órgão judicial competente.
Formatar o número do processo respeitando a seguinte formatação:
NNNNNNN-DD.AAAA.J.TR.OOOO . A identificação do número do processo foi
estabelecida pelo CNJ da seguinte forma:

==\> Número sequencial (NNNNNNN): Os primeiros 7 dígitos são um
identificador único do processo.

==\> Dígito verificador (DD): Os 2 dígitos seguintes funcionam para a
verificação do código.

==\> Ano de ajuizamento (AAAA): Os 4 dígitos seguintes correspondem ao
ano em que a ação foi protocolada.

==\> Código do segmento da Justiça (J): O dígito seguinte identifica o
ramo do Judiciário, como Justiça Federal (4), Justiça do Trabalho (5) ou
Justiça Estadual (8).

==\> Código do Tribunal (TR): Os 2 dígitos seguintes indicam o tribunal
de origem.

==\> Código da unidade de origem (OOOO): Os últimos 4 dígitos
identificam a comarca, seção judiciária ou unidade de origem do
processo.

O cadastro de processos deverá ter os seguintes campos:

- Cadastro de Processos com os seguintes campos:

- Número CNJ - Número do Processo

- Local de trâmite

- Status processual

- Comarca

- Área de atuação - Civil ou Trabalhista

- Fase

- \- 1a. Instância: Postulatória / Saneadora / Instrutória / Decisória

- \- 2a. Instância

- Objeto da ação (nome dado ao processo)

- Responsável

- Assunto

- Valor da causa

- Encerramento

- Sentença

- Distribuição

- Execução

- Segredo de justiça - sim / não

- ==\> Ficha para registrar as movimentações no cadastro do processo

- ==\> Lançamento automático na Ficha do Processo toda vez que houver
  uma movimentação.

2\. Após a criação do número do processo, conforme mencionado acima, não
se permite mais que o número seja alterado.

3\. No momento da criação de um novo caso jurídico contencioso deve-se
criar o cadastro da Parte Adversa (que pode ser Réu ou Autor, conforme
dados abaixo:

- Nome

- Nacionalidade

- Profissão

- Estado civil

- CEP - (busca)

- Estado

- Cidade

- Bairro

- CPF

- RG

- Email

- Telefone

- Nome da mãe

4\. Quando o Escritório de Advocacia receber um novo cliente que esteja
trazendo um ou mais processos já em andamento, o app deverá permitir a
inclusão destes processos via formato CSV.

5\. O cadastro de clientes deverá registrar -- além dos campos descritos
ao final deste item - em campo específico, e de forma isolada, todos os
documentos que dão sustentação ao caso jurídico contencioso, documentos
estes que foram alimentados no processo de RAG. Cadastro de Clientes:

- Cadastro de Clientes deverá conter os seguintes campos:

- Tipo: Física / Jurídica

- Nome

- Profissão

- Estado Civil

- CEP - (busca)

- Cidade

- Estado

- CPF

- RG

- Email

- Telefone

- Nome da Mãe

- ==\> Ficha para registrar as movimentações realizadas no cadastro do
  cliente.

- ==\> Agendamento do cliente

6\. Além dos campos mencionados no item 5 acima, o cadastro de clientes
deve ter campos específicos para receber o Resumo do Caso, da Análise
Estratégica (\'Identificar Riscos Legais\' e \'Sugerir Próximos
Passos\'), Análise FIRAC e Petições. Caso surjam novos documentos
ingeridos no processo RAG, estes campos serão atualizados após o
Escritório de Advocacia executar cada uma destas funcionalidades.

7\. Diariamente o app deverá executar automaticamente as tarefas
descritas em \'Implementação de Comunicações Processuais\', utilizando
para isto o número do processo -- ver código '**robot_pje_v2.py**'

8\. A KB Global deverá permitir todos os recursos de CRUD, assim como
deverá permitir a classificação adotada pelo Escritório para separação
dos documentos ingeridos - por exemplo: Processos Civil - Processos
Trabalhistas - Doutrinas Vigentes, etc

9\. Atualmente o app gera somente a Petição Inicial. Com esta nova
implementação, será criada uma área específica para Petições, com foco
nas áreas Civil e Trabalhista. De acordo com o andamento do processo o
app deverá disponibilizar a Petição correspondente, alimentando
automaticamente as informações pertinentes àquela Petição.

10\. Todas as alterações acima deverão ter como referência a
implementação final do app para o modelo SaaS multi-tenant.
