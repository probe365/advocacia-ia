### **Alterações a Serem Feitas no Projeto 'Advocacia e IA':**

1\. Permitir a inclusão do número do processo após a abertura do caso, quando se tratar de um processo inicial. O número de 20 dígitos de um processo judicial é gerado no momento em que a petição inicial é protocolada e o processo é registrado na distribuição do órgão judicial competente. Formatar o número do processo respeitando a seguinte formatação: NNNNNNN-DD.AAAA.J.TR.OOOO . A identificação do número do processo foi estabelecida pelo CNJ da seguinte forma:

==> Número sequencial (AAAAAAA): Os primeiros 7 dígitos são um identificador único do processo.

==> Dígito verificador (DD): Os 2 dígitos seguintes funcionam para a verificação do código.

==> Ano de ajuizamento (AAAA): Os 4 dígitos seguintes correspondem ao ano em que a ação foi protocolada.

==> Código do segmento da Justiça (J): O dígito seguinte identifica o ramo do Judiciário, como Justiça Federal (4), Justiça do Trabalho (5) ou Justiça Estadual (8).

==> Código do Tribunal (TT): Os 2 dígitos seguintes indicam o tribunal de origem.

==> Código da unidade de origem (UUUU): Os últimos 4 dígitos identificam a comarca, seção judiciária ou unidade de origem do processo.



2\. Após a criação do número do processo, conforme mencionado acima, não se permite mais que o número seja alterado.



3\. No momento da criação de um novo caso jurídico contencioso deve-se cadastrar também as informações da pessoa(s) ou empresa(s) que serão acionadas. Estas informações devem incluir: nome completo, endereço completo, CPF/CNPJ e, no caso de empresas, o nome do responsável.



4\. Quando o Escritório de Advocacia receber um novo cliente que esteja trazendo um ou mais processos já em andamento, estas informações deverão estar do formato CSV para que sejam cadastradas no app em uma única vez. Estas informações devem incluir: ***VER. DANIEL KELETY***



5\. Após o cadastramento de um novo cliente e seus processos jurídicos, o app deverá usar o número do processo para acessar os Tribunais correspondentes para obter as certidões que validam os processos trazidos pelo novo cliente, conforme mencionado no item 4 acima. O Código do Tribunal (TT) mencionado no item 1 acima servirá como referência para busca destas informações. ***VER. DANIEL KELETY***



6\. O cadastro de um novo cliente deverá registrar - além dos campos de identificação, endereço, etc - em campo específico, e de forma isolada, todos os documentos que dão sustentação do caso jurídico contencioso, documentos estes que foram alimentados no processo de RAG. Toda a alimentação de informações sobre o caso jurídico contencioso deverá ser feita em ordem cronológica. ***VER. DANIEL KELETY***



7\. Além dos campos mencionados no item 6 acima, o cadastro de um novo cliente deve ter campos específicos para receber o Resumo do Caso, da Análise Estratégica ('Identificar Riscos Legais' e 'Sugerir Próximos Passos'), Análise FIRAC e Petições. Caso surjam novos documentos ingeridos no processo RAG, estes campos serão atualizados após o Escritório de Advocacia executar cada uma destas funcionalidades.



8\. Diariamente o app deverá executar automaticamente as tarefas descritas em 'Implementação de Comunicações Processuais'.



9\. A KB Global deverá permitir todos os recursos de CRUD, assim como deverá permitir a classificação adotada pelo Escritório para separação dos documentos ingeridos - por exemplo: Processos Civil - Processos Trabalhistas - Doutrinas Vigentes, etc



10\. Atualmente o app gera somente a Petição Inicial. Com esta nova implementação, será criada uma área específica para Petições, com foco nas áreas Civil e Trabalhista. De acordo com o andamento do  processo o app deverá disponibilizar a Petição correspondente, alimentando automaticamente as informações pertinentes àquela Petição.



11\. Todas as alterações acima deverão ter como referência a implementação final do app para o modelo SaaS multi-tenant.



\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

#### **Implementação de Comunicações Processuais:**



1\. Em nosso app há um cliente do Escritório que tem o processo de número 4002107-38.2025.8.26.0562

2\. Diariamente o advogado copia o número de 20 dígitos do processo;

3\. Diariamente o CNJ através do website https://comunica.pje.jus.br/ publica Comunicações Processuais em todo o país para que as partes envolvidas em processo jurídico contencioso sejam notificadas sobre decisões tomadas pelos tribunais de cada localidade. Advogados devem, diariamente, tomar conhecimento destas comunicações, e têm prazos para responderem aos termos contidos nestas comunicações.

4\. O acesso a uma comunicação específica, direcionada a um advogado é feito da seguinte forma:

4.1 - O advogado acessa o website mencionado acima;

4.2 - Diariamente, no campo de buscas, digita o número do processo.

4.3 - O sistema retorna com comunicação existente, caso haja alguma, fornecendo os detalhes da Sentença nela contidos;

4.4 - O advogado copia o endereço contido no navegador;

4.4 - O advogado clica sobre o botão 'Copiar sem formatação' para copiar para área específica;

4.5 -

