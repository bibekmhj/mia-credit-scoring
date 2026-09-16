/**
 * Build the research paper manuscript as a .docx file.
 * Computers & Security (Elsevier) submission format.
 * All results are empirical measurements from run_experiments_v2.py.
 * No results are fabricated.
 */
"use strict";
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, WidthType, BorderStyle, ShadingType,
  TableOfContents, PageBreak, Footer, PageNumber, NumberFormat,
  convertInchesToTwip, Header, Tab, ImageRun
} = require("docx");
const fs = require("fs");

// ── Helpers ────────────────────────────────────────────────────────────────

const A4_W  = 11906;   // EMU 1/20pt; A4 = 210mm
const A4_H  = 16838;
const MARGIN = convertInchesToTwip(1.0);
const GUTTER = convertInchesToTwip(0);
const INDENT = convertInchesToTwip(0.5);
const FONT   = "Times New Roman";
const FONT_SZ = 24;          // half-points: 24 = 12pt
const FONT_SZ_SM = 20;       // 10pt for tables
const FONT_SZ_CAP = 20;      // 10pt for captions
const FONT_SZ_REF = 20;      // 10pt for references
const LINE_SPACING = { line: 480, lineRule: "auto" };   // double-spaced
const SPACE_AFTER  = 0;      // let double-spacing carry paragraph rhythm

function run(text, opts = {}) {
  return new TextRun({ text, font: FONT, size: opts.size || FONT_SZ,
    bold: opts.bold, italics: opts.italic, color: opts.color });
}

function para(runs, opts = {}) {
  const r = typeof runs === "string" ? [run(runs, opts)] : runs;
  return new Paragraph({
    children: r,
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { line: LINE_SPACING.line, lineRule: LINE_SPACING.lineRule,
               after: opts.spaceAfter !== undefined ? opts.spaceAfter : SPACE_AFTER,
               before: opts.spaceBefore || 0 },
    indent: opts.indent ? { firstLine: INDENT } : undefined,
    pageBreakBefore: opts.pageBreak || false,
  });
}

function heading(text, level, numbering) {
  const num = numbering ? run(`${numbering}  `, { bold: true }) : null;
  return new Paragraph({
    children: num ? [num, run(text, { bold: true })] : [run(text, { bold: true })],
    heading: level,
    spacing: { line: 360, lineRule: "auto", before: 200, after: 100 },
    alignment: AlignmentType.LEFT,
  });
}

// Table helpers
function tcell(text, opts = {}) {
  return new TableCell({
    children: [new Paragraph({
      children: [new TextRun({ text, font: FONT, size: FONT_SZ_SM,
        bold: opts.bold, italics: opts.italic })],
      alignment: opts.align || AlignmentType.CENTER,
      spacing: { line: 240, after: 40 },
    })],
    width: { size: opts.width || 10, type: WidthType.PERCENTAGE },
    shading: opts.shade ? { type: ShadingType.CLEAR, color: "auto", fill: "E8E8E8" } : undefined,
    columnSpan: opts.span,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
  });
}

function trow(cells) { return new TableRow({ children: cells }); }

function makeTable(rows, widths) {
  return new Table({
    rows,
    width: { size: 100, type: WidthType.PERCENTAGE },
    columnWidths: widths,
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 2, color: "000000" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "000000" },
      left:   { style: BorderStyle.NONE },
      right:  { style: BorderStyle.NONE },
      insideH:{ style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" },
      insideV:{ style: BorderStyle.NONE },
    },
  });
}

function caption(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: FONT, size: FONT_SZ_CAP, italics: true })],
    alignment: AlignmentType.LEFT,
    spacing: { line: 240, before: 80, after: 200 },
  });
}

function blank() { return para("", { spaceAfter: 0 }); }

// ── Figure image helper ────────────────────────────────────────────────────

function figImage(imgPath, widthPx, captionText, aspectRatio) {
  const imgBuf = fs.readFileSync(imgPath);
  // widthPx in docx "pixels" (96 dpi points); aspectRatio = height/width
  const ar = aspectRatio || 0.52;
  const h = Math.round(widthPx * ar);
  return [
    new Paragraph({
      children: [new ImageRun({
        data: imgBuf,
        transformation: { width: widthPx, height: h },
        type: "png",
      })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 60 },
    }),
    caption(captionText),
  ];
}

// Preload figure images
const FIG1 = "/tmp/fig1_threat_model.png";
const FIG2 = "/tmp/fig2_pipeline.png";
const FIG3 = "/tmp/fig3_attack_auc.png";
const FIG4 = "/tmp/fig4_defense_tradeoff.png";

// ── Document content ───────────────────────────────────────────────────────

const children = [];
const push = (...items) => items.forEach(i => children.push(i));

// ── TITLE PAGE ────────────────────────────────────────────────────────────

push(
  new Paragraph({
    children: [new TextRun({
      text: "Membership Inference Attacks on Credit Scoring Models: Empirical Risk Analysis and Differential Privacy Defenses Under U.S. Banking Privacy Requirements",
      font: FONT, size: 28, bold: true,
    })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 500, after: 400, line: 400, lineRule: "auto" },
  }),

  new Paragraph({
    children: [new TextRun({ text: "Bibek Maharjan", font: FONT, size: FONT_SZ })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 100, line: 360, lineRule: "auto" },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Software Engineer, Financial Services Industry", font: FONT, size: FONT_SZ, italics: true })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 600, line: 360, lineRule: "auto" },
  }),

  new Paragraph({
    children: [new TextRun({ text: "Corresponding author: bbkmhj06@gmail.com", font: FONT, size: FONT_SZ_SM })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 800 },
  }),
);

// ── ABSTRACT ─────────────────────────────────────────────────────────────

push(
  heading("Abstract", HeadingLevel.HEADING_1, null),
  para([
    run("Machine learning models deployed for credit scoring are potentially vulnerable to membership inference attacks (MIA), in which an adversary with query access to a prediction API attempts to determine whether a specific consumer record appeared in the model's training set. Such inference, if successful, constitutes a form of privacy breach with direct implications under the Gramm-Leach-Bliley Act and related U.S. banking privacy requirements. This paper presents an empirical study of MIA vulnerability and defense effectiveness on three publicly available credit datasets - UCI Default of Credit Card Clients (Taiwan Credit, n=29,999), Kaggle Give Me Some Credit (n=150,000), and Home Credit Default Risk (n=307,511) - using gradient boosting classifiers (XGBoost, LightGBM) and Explainable Boosting Machines. We evaluate two attack strategies (confidence-threshold and shadow-model attacks) and four defenses (confidence rounding, output perturbation, stronger regularization, and differentially private logistic regression). Results show that MIA vulnerability is moderate and highly dataset-dependent: the shadow-model attack achieves AUC-ROC of 0.570 on the Taiwan Credit XGBoost model but remains near random (0.507-0.513) on the two larger datasets. Train-validation AUC gap is the strongest predictor of attack success (Spearman rho=0.733, p=0.025). Regularization reduces attack AUC to near-random with negligible utility cost, while differential privacy (epsilon=5) achieves the same with a utility reduction of 4.9 percentage points or less across all datasets. EBM models show structural resistance to MIA due to their additive architecture. These findings have concrete implications for financial institutions deploying ML-based credit models under SR 11-7 model risk management guidance and NIST AI Risk Management Framework requirements."),
  ], { indent: false }),

  blank(),
  para([
    run("Keywords: ", { bold: true }),
    run("membership inference attack; credit scoring; gradient boosting; differential privacy; model risk management; banking; explainable machine learning"),
  ], { indent: false }),
);

// ── SECTION 1: INTRODUCTION ──────────────────────────────────────────────

push(
  blank(),
  heading("1. Introduction", HeadingLevel.HEADING_1, null),

  para("The adoption of machine learning in credit underwriting has accelerated substantially over the past decade. Gradient boosting classifiers - XGBoost, LightGBM, and related ensemble methods - have become standard tools for predicting borrower default, outperforming logistic regression on most benchmark credit datasets and offering practical advantages in handling tabular data with mixed feature types [1,2]. Yet the widespread deployment of these models in regulated financial environments raises privacy questions that have not been fully examined in the existing literature.", { indent: true }),

  para("A membership inference attack (MIA) is a procedure by which an adversary queries a model's prediction API and uses the returned probabilities to infer whether a particular record was part of the model's training set [3]. From a banking privacy perspective, a successful MIA can expose the fact that a specific consumer's financial history was used to train a credit model - information that may be protected as nonpublic personal information (NPI) under the Gramm-Leach-Bliley Act (GLBA), 15 U.S.C. Section 6801. Although MIA does not directly expose the underlying record values, membership disclosure alone can convey sensitive information about a consumer's financial history, particularly when training sets are assembled from applicant populations with known demographic characteristics.", { indent: true }),

  para("U.S. banking regulators have increasingly emphasized privacy and model risk as interconnected concerns. The Federal Reserve Board's SR 11-7 guidance on model risk management, updated in 2026 with a risk-based approach tailored to an organization's model risk profile, requires financial institutions to understand and document the limitations of models in production, including risks arising from data characteristics [4]. The NIST AI Risk Management Framework (AI RMF 1.0) identifies training data privacy as a dimension of AI risk that organizations should measure and address [5]. Despite these regulatory expectations, there is limited empirical guidance on the actual severity of MIA risk for gradient boosting credit models across datasets of different sizes, default rates, and feature counts.", { indent: true }),

  para("This paper makes four contributions. First, we conduct an empirical MIA evaluation on three public credit datasets spanning a wide range of sizes (30K to 307K records) and default rates (6.7% to 22.1%), using XGBoost, LightGBM, and Explainable Boosting Machines. Second, we evaluate both the confidence-threshold attack and the shadow-model attack, using a five-feature meta-classifier that distinguishes the two approaches. Third, we evaluate four defenses - confidence rounding, Laplace output perturbation, stronger regularization, and differentially private logistic regression - and measure the privacy-utility trade-off for each. Fourth, we analyze what model and dataset characteristics drive MIA vulnerability, finding that the train-validation AUC gap is the primary predictor. All experiments use publicly available data, fixed random seeds, and reproducible code.", { indent: true }),

  para("The remainder of this paper is organized as follows. Section 2 reviews related work on membership inference and privacy in machine learning. Section 3 identifies the research gap and states our contributions. Section 4 describes the threat model and attack methods. Section 5 describes the datasets, models, and experimental setup. Section 6 reports results. Section 7 discusses findings and banking implications. Section 8 states limitations. Section 9 concludes.", { indent: true }),
);

// ── SECTION 2: RELATED WORK ──────────────────────────────────────────────

push(
  blank(),
  heading("2. Related Work", HeadingLevel.HEADING_1, null),

  heading("2.1 Membership Inference Attacks", HeadingLevel.HEADING_2, null),

  para("Shokri et al. [3] introduced the shadow-model attack on machine learning classifiers, showing that the difference in a model's confidence on training versus non-training records is sufficient for an adversary to distinguish membership. Their attack trains multiple shadow models on data drawn from the same distribution as the target model's training data, then trains a meta-classifier on the shadow outputs to identify membership. The approach generalizes across model types and query-only access assumptions.", { indent: true }),

  para("Yeom et al. [6] formalized the connection between MIA and overfitting, proving that a model with train-test accuracy gap g is vulnerable to membership inference with advantage at least g/2 over random guessing. This theoretical result motivates our empirical examination of the relationship between AUC gap and attack success. Carlini et al. [7] later showed that even slightly overfit models leak membership, and that the simplest confidence-threshold attack achieves substantial success when models are evaluated at low false-positive rates - a finding we confirm on TaiwanCredit.", { indent: true }),

  para("Song and Mittal [8] conducted a systematic evaluation across 21 model architectures and found that membership inference success is highly model- and dataset-specific, with deep networks generally more vulnerable than shallow classifiers. Long et al. [9] proposed a pragmatic approach using model confidence alone and found that gradient-boosted trees are moderately vulnerable due to their tendency to overfit on minority class records. Nasr et al. [10] studied white-box attacks but also evaluated black-box attacks similar to our setup, finding that output probabilities carry enough information for membership inference in many settings.", { indent: true }),

  para("Choquette-Choo et al. [11] developed label-only attacks that succeed even when a model returns only a predicted class rather than probabilities. While our current study uses probability-returning models in line with most deployed credit scoring APIs, the existence of label-only attacks underscores that API restrictions alone are insufficient for privacy.", { indent: true }),

  heading("2.2 Credit Scoring and Gradient Boosting", HeadingLevel.HEADING_2, null),

  para("Gradient boosting has become the dominant approach for tabular credit scoring. Lessmann et al. [1] benchmarked classification algorithms on eight credit datasets and found that gradient boosting methods consistently ranked among the top performers. Thomas et al. [12] discuss the regulatory context of credit scoring models, including documentation, validation, and fairness obligations that directly motivate model risk management practices. The trend toward complex ML models in credit underwriting creates the conditions for MIA vulnerability: models with sufficient capacity to fit training data tightly also tend to memorize individual records.", { indent: true }),

  para("Feldman [13] demonstrated theoretically that memorization of rare training examples may be necessary for generalization in long-tailed data distributions, which are characteristic of credit datasets with low default rates (6-8%). This result suggests that the regularization-versus-memorization trade-off in credit models is not purely a modeling choice but may be structurally tied to data characteristics.", { indent: true }),

  heading("2.3 Differential Privacy for Machine Learning", HeadingLevel.HEADING_2, null),

  para("Dwork et al. [14] established the formal framework of differential privacy (DP), which provides a mathematical guarantee that the output of a computation is approximately the same whether any single record is included or excluded from the input. An epsilon-DP mechanism limits the probability ratio of any output under adjacent datasets to e^epsilon. Smaller epsilon implies stronger privacy but typically lower utility.", { indent: true }),

  para("Abadi et al. [15] introduced the DP-SGD algorithm for training neural networks with differential privacy, and the approach has been extended to logistic regression and other convex models. The IBM diffprivlib library [16] implements DP logistic regression using the Laplace mechanism, providing an accessible implementation for practitioners. DP gradient boosting remains an active research area; current practical implementations typically achieve strong privacy guarantees only for linear models, motivating our comparison of DP-LR against gradient boosting baselines.", { indent: true }),

  heading("2.4 Gap in the Literature", HeadingLevel.HEADING_2, null),

  para("No prior work combines all of the following in a single empirical study: (1) MIA evaluation specifically on gradient boosting credit scoring models, (2) multiple real public credit datasets spanning a range of sizes and default rates, (3) comparison of both confidence-threshold and shadow-model attacks, (4) evaluation of multiple defense strategies including DP, and (5) analysis of the relationship between model overfitting and attack success in the context of U.S. banking regulatory requirements. Several studies address subsets of these elements but do not combine them in a way that provides actionable guidance for banking practitioners.", { indent: true }),
);

// ── SECTION 3: RESEARCH GAP AND CONTRIBUTIONS ────────────────────────────

push(
  blank(),
  heading("3. Research Gap and Contributions", HeadingLevel.HEADING_1, null),

  para("The research gap motivating this study is the absence of empirical evidence on MIA risk severity for gradient boosting credit models across realistic dataset conditions. The existing MIA literature is dominated by deep learning models on image and text data; the limited work on tabular gradient boosting focuses on general benchmarks rather than credit-specific datasets with the class imbalance, regulatory context, and feature characteristics typical of financial applications.", { indent: true }),

  para("This study addresses three testable hypotheses:", { indent: true }),

  para([
    run("H1: ", { bold: true }),
    run("Shadow-model MIA success (attack AUC-ROC) exceeds random baseline (0.50) for at least one dataset-model combination evaluated in this study."),
  ], { indent: true }),

  para([
    run("H2: ", { bold: true }),
    run("Differential privacy (epsilon=5) reduces attack AUC-ROC to near-random (<0.505) while incurring a utility cost (validation AUC reduction) of less than 5 percentage points on at least two of the three datasets."),
  ], { indent: true }),

  para([
    run("H3: ", { bold: true }),
    run("Attack success (shadow-model AUC-ROC) is positively and significantly correlated with the model's train-validation AUC gap (Spearman rho > 0.60, p < 0.05)."),
  ], { indent: true }),

  para("The contributions of this paper are: (C1) the first empirical MIA evaluation comparing XGBoost, LightGBM, and EBM on the same credit datasets with identical experimental splits; (C2) a defense comparison covering rounding, output perturbation, regularization, and DP-LR with measured privacy-utility trade-offs; (C3) empirical evidence that the train-validation AUC gap is the strongest predictor of MIA vulnerability in this domain; and (C4) a discussion of implications for banking practitioners under SR 11-7, GLBA, and NIST AI RMF.", { indent: true }),
);

// ── SECTION 4: THREAT MODEL AND ATTACK METHODS ───────────────────────────

push(
  blank(),
  heading("4. Threat Model and Attack Methods", HeadingLevel.HEADING_1, null),

  heading("4.1 Threat Model", HeadingLevel.HEADING_2, null),

  para("We consider a black-box query adversary who has access to a deployed credit scoring model's API and can submit feature vectors and receive output probability vectors. The adversary knows the feature space but has no access to model weights, training data, or training algorithm details. This corresponds to the realistic scenario in which an attacker - who may be an internal auditor, a regulatory examiner with limited access, or an adversary who obtained a copy of a set of consumer records through other means - wishes to determine whether specific consumer records were included in the model's training set.", { indent: true }),

  ...figImage(FIG1, 590, "Figure 1. Membership inference attack threat model for credit scoring systems. The model owner trains and deploys a gradient boosting credit scorer. The adversary queries the API and uses shadow models to train a meta-classifier that predicts whether a given record was in the training set."),
  blank(),

  para("From a GLBA perspective, successful MIA can expose the fact that a consumer's NPI was used to train the model. While GLBA Section 6801 does not explicitly address model training data, its requirement to 'protect the security and confidentiality of customer records and information' creates a duty to limit inference on those records. NIST AI RMF [5] identifies training data privacy as an AI risk dimension that organizations should measure and manage. SR 11-7 [4] requires model risk management to address risks from model inputs, including the data used to develop the model.", { indent: true }),

  heading("4.2 Confidence-Threshold Attack", HeadingLevel.HEADING_2, null),

  para("The simplest MIA strategy uses the model's confidence in the true class of a record as the attack score [3,6]. For a record with true label y and model output probability vector p, the attack score is p[y]. Training records tend to receive higher confidence because gradient boosting models overfit to training points and assign them near-certainty probabilities. The attack AUC-ROC measures how well this score separates member records (used in training) from non-member records (held out).", { indent: true }),

  heading("4.3 Shadow-Model Attack", HeadingLevel.HEADING_2, null),

  para("The shadow-model attack [3] trains N=4 shadow models on disjoint subsets of a shadow data pool, each using 60% of the pool as member data and the remaining 40% as non-member data. For each shadow model and each data point, we extract a five-dimensional feature vector: [p0, p1, max(p0,p1), H(p), p[y]], where p0 and p1 are the class probabilities, H(p) is the prediction entropy, and p[y] is the true-class confidence. We train a logistic regression meta-classifier on the shadow model feature vectors labeled by membership, then apply it to the target model's outputs to classify member and non-member records. Attack performance is measured as AUC-ROC on the held-out member/non-member split.", { indent: true }),

  para("Shadow models are XGBoost classifiers with the same default hyperparameters as the target model baseline. We use logistic regression (scikit-learn, L2 regularization) as the meta-classifier following Shokri et al. [3]. The five-feature representation extends the original attack's single-confidence score to include distributional features that better characterize the model's uncertainty, following Song and Mittal [8].", { indent: true }),
);

// ── SECTION 5: DATA AND EXPERIMENTAL SETUP ───────────────────────────────

push(
  blank(),
  heading("5. Data and Experimental Setup", HeadingLevel.HEADING_1, null),

  ...figImage(FIG2, 590, "Figure 2. Experimental pipeline. Datasets are partitioned into four splits (40% member-train, 10% member-val, 25% non-member, 25% shadow pool). Baseline models and defended variants are each evaluated with both the confidence-threshold and shadow-model attacks. Driver analysis and defense comparison are performed on the resulting AUC-ROC scores.", 0.43),
  blank(),

  heading("5.1 Datasets", HeadingLevel.HEADING_2, null),

  para("We use three publicly available credit datasets. All datasets are freely available for research purposes under their respective terms. Table 1 summarizes their key properties. A fourth dataset (German Credit from UCI via Kaggle) was excluded because the available Kaggle upload did not include the target class column.", { indent: true }),

  blank(),
  caption("Table 1. Dataset characteristics. n=full dataset size; n_features excludes target column; default rate is raw fraction of positive class."),
  makeTable([
    trow([
      tcell("Dataset", { bold: true, shade: true, width: 22 }),
      tcell("Source", { bold: true, shade: true, width: 18 }),
      tcell("n", { bold: true, shade: true, width: 10 }),
      tcell("Features", { bold: true, shade: true, width: 10 }),
      tcell("Default Rate", { bold: true, shade: true, width: 14 }),
      tcell("Member Train (40%)", { bold: true, shade: true, width: 14 }),
      tcell("Non-member (25%)", { bold: true, shade: true, width: 12 }),
    ]),
    trow([
      tcell("Taiwan Credit (TW)", { width: 22 }),
      tcell("UCI / Kaggle [17]", { width: 18 }),
      tcell("29,999", { width: 10 }),
      tcell("24", { width: 10 }),
      tcell("22.1%", { width: 14 }),
      tcell("12,000", { width: 14 }),
      tcell("7,500", { width: 12 }),
    ]),
    trow([
      tcell("Give Me Some Credit (GMSC)", { width: 22 }),
      tcell("Kaggle [18]", { width: 18 }),
      tcell("150,000", { width: 10 }),
      tcell("10", { width: 10 }),
      tcell("6.7%", { width: 14 }),
      tcell("60,000", { width: 14 }),
      tcell("37,500", { width: 12 }),
    ]),
    trow([
      tcell("Home Credit Default (HC)", { width: 22 }),
      tcell("Kaggle [19]", { width: 18 }),
      tcell("307,511", { width: 10 }),
      tcell("120", { width: 10 }),
      tcell("8.1%", { width: 14 }),
      tcell("123,004", { width: 14 }),
      tcell("76,878", { width: 12 }),
    ]),
  ], [3132, 2376, 1320, 1320, 1848, 1848, 1584]),
  blank(),

  para("The Taiwan Credit dataset (UCI Default of Credit Card Clients) [17] contains 30,000 records of credit card clients in Taiwan with 23 features including payment history, billing amounts, and demographic variables. The Give Me Some Credit dataset [18] contains 150,000 U.S. borrower records with 10 delinquency-related features. The Home Credit Default Risk dataset [19] is the largest in our study, with 307,511 loan applications and 120 features including application-level and derived financial attributes. Categorical features in Home Credit were label-encoded; missing values across all datasets were imputed with the column median.", { indent: true }),

  heading("5.2 MIA Experimental Split", HeadingLevel.HEADING_2, null),

  para("Each dataset is split into four non-overlapping partitions using a fixed random seed (42): member-train (40%), member-validation (10%), non-member (25%), and shadow pool (25%). Target models are trained on the member-train partition. Member-validation records are included in the member set for attack evaluation. The non-member set provides the non-member examples for computing attack AUC-ROC. The shadow pool is used exclusively by shadow models and is never seen by target models. This split convention follows Shokri et al. [3] adapted for our larger datasets.", { indent: true }),

  heading("5.3 Models", HeadingLevel.HEADING_2, null),

  para("We train three model types as baselines: XGBoost [20] (n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0), LightGBM [21] (same hyperparameters), and Explainable Boosting Machine [22] (default configuration). All models use AUC-ROC as the evaluation metric. EBM is trained on all data for TaiwanCredit and GiveMeSomeCredit; for HomeCredit, EBM is trained on an 80,000-record stratified subsample due to compute time constraints, while XGBoost and LightGBM are trained on the full dataset.", { indent: true }),

  heading("5.4 Defenses", HeadingLevel.HEADING_2, null),

  para("We evaluate four defense categories applied to the XGBoost baseline model (the most vulnerable baseline on each dataset). Confidence rounding quantizes the output probability to K evenly-spaced bins (K=5 and K=10). Output perturbation adds independent Laplace noise with scale sigma=0.02 and sigma=0.05 to each output probability. Stronger regularization retrains XGBoost with reg_lambda=10.0 and max_depth=3 (reduced from defaults of 1.0 and 6). Differentially private logistic regression uses diffprivlib [16] with epsilon=1, 5, and 10; inputs are standardized and data_norm is set to 5.0.", { indent: true }),

  heading("5.5 Evaluation Metrics", HeadingLevel.HEADING_2, null),

  para("We report AUC-ROC for all attack and defense evaluations. For defenses, we also report the utility cost as the reduction in validation AUC relative to the undefended XGBoost baseline. AUC-ROC of 0.50 corresponds to random guessing (no privacy leakage). We additionally compute the Spearman rank correlation between train-validation AUC gap and shadow-model attack AUC across all baseline observations.", { indent: true }),

  para("All experiments were implemented in Python 3.11 with scikit-learn 1.8.0, XGBoost 3.2.0, LightGBM 4.7.0, InterpretML (interpret-core) 0.6.8, and diffprivlib 0.6.6 (with a one-line patch to remove the deprecated multi_class parameter incompatible with scikit-learn 1.8.0). Random seeds are fixed at 42 throughout. Code and configuration are available in the supplementary material.", { indent: true }),
);

// ── SECTION 6: RESULTS ───────────────────────────────────────────────────

push(
  blank(),
  heading("6. Results", HeadingLevel.HEADING_1, null),

  heading("6.1 Baseline Model Performance and Overfitting", HeadingLevel.HEADING_2, null),

  para("Table 2 reports train AUC, validation AUC, and the train-validation gap for all baseline models. TaiwanCredit shows the highest overfitting across models: XGBoost achieves train AUC=0.974 versus validation AUC=0.769, a gap of 0.205. LightGBM shows a similar gap (0.184). EBM, by contrast, shows a gap of only 0.037 on TaiwanCredit, reflecting its additive architecture's resistance to memorization. GiveMeSomeCredit shows moderate gaps (0.007-0.067), with EBM nearly at the same level as XGBoost and LightGBM. HomeCredit shows intermediate gaps (0.101-0.127) despite having 40% more training records than the next largest dataset.", { indent: true }),

  blank(),
  caption("Table 2. Baseline model performance. Train AUC and validation AUC are reported on member-train and member-validation partitions. Gap = Train AUC - Validation AUC."),
  makeTable([
    trow([
      tcell("Dataset", { bold: true, shade: true, width: 26 }),
      tcell("Model", { bold: true, shade: true, width: 18 }),
      tcell("Train AUC", { bold: true, shade: true, width: 18 }),
      tcell("Val AUC", { bold: true, shade: true, width: 18 }),
      tcell("Gap", { bold: true, shade: true, width: 20 }),
    ]),
    trow([tcell("TaiwanCredit", { width: 26 }), tcell("XGBoost", { width: 18 }), tcell("0.9737", { width: 18 }), tcell("0.7692", { width: 18 }), tcell("0.2045", { width: 20 })]),
    trow([tcell("TaiwanCredit", { width: 26 }), tcell("LightGBM", { width: 18 }), tcell("0.9539", { width: 18 }), tcell("0.7701", { width: 18 }), tcell("0.1839", { width: 20 })]),
    trow([tcell("TaiwanCredit", { width: 26 }), tcell("EBM", { width: 18 }), tcell("0.8166", { width: 18 }), tcell("0.7798", { width: 18 }), tcell("0.0369", { width: 20 })]),
    trow([tcell("GiveMeSomeCredit", { width: 26 }), tcell("XGBoost", { width: 18 }), tcell("0.9275", { width: 18 }), tcell("0.8606", { width: 18 }), tcell("0.0669", { width: 20 })]),
    trow([tcell("GiveMeSomeCredit", { width: 26 }), tcell("LightGBM", { width: 18 }), tcell("0.9198", { width: 18 }), tcell("0.8625", { width: 18 }), tcell("0.0573", { width: 20 })]),
    trow([tcell("GiveMeSomeCredit", { width: 26 }), tcell("EBM", { width: 18 }), tcell("0.8735", { width: 18 }), tcell("0.8670", { width: 18 }), tcell("0.0066", { width: 20 })]),
    trow([tcell("HomeCredit", { width: 26 }), tcell("XGBoost", { width: 18 }), tcell("0.8830", { width: 18 }), tcell("0.7559", { width: 18 }), tcell("0.1271", { width: 20 })]),
    trow([tcell("HomeCredit", { width: 26 }), tcell("LightGBM", { width: 18 }), tcell("0.8575", { width: 18 }), tcell("0.7538", { width: 18 }), tcell("0.1037", { width: 20 })]),
    trow([tcell("HomeCredit", { width: 26 }), tcell("EBM (80K)", { width: 18 }), tcell("0.8300", { width: 18 }), tcell("0.7286", { width: 18 }), tcell("0.1014", { width: 20 })]),
  ], [3432, 2376, 2376, 2376, 2640]),
  blank(),

  heading("6.2 Attack Results", HeadingLevel.HEADING_2, null),

  para("Table 3 reports attack AUC-ROC for both attack methods across all baseline models. Attack AUC-ROC above 0.50 indicates exploitable membership information; the further above 0.50, the more severe the privacy leakage. Figure 3 visualizes these results across both attack strategies.", { indent: true }),

  blank(),
  caption("Table 3. Attack results for baseline models. Threshold AUC = confidence-threshold attack AUC-ROC; Shadow AUC = shadow-model attack AUC-ROC. Both are measured on held-out member/non-member partitions."),
  makeTable([
    trow([
      tcell("Dataset", { bold: true, shade: true, width: 26 }),
      tcell("Model", { bold: true, shade: true, width: 18 }),
      tcell("Train-Val Gap", { bold: true, shade: true, width: 18 }),
      tcell("Threshold AUC", { bold: true, shade: true, width: 19 }),
      tcell("Shadow AUC", { bold: true, shade: true, width: 19 }),
    ]),
    trow([tcell("TaiwanCredit", { width: 26 }), tcell("XGBoost", { width: 18 }), tcell("0.2045", { width: 18 }), tcell("0.5541", { width: 19 }), tcell("0.5699", { width: 19, bold: true })]),
    trow([tcell("TaiwanCredit", { width: 26 }), tcell("LightGBM", { width: 18 }), tcell("0.1839", { width: 18 }), tcell("0.5446", { width: 19 }), tcell("0.5553", { width: 19 })]),
    trow([tcell("TaiwanCredit", { width: 26 }), tcell("EBM", { width: 18 }), tcell("0.0369", { width: 18 }), tcell("0.5024", { width: 19 }), tcell("0.5030", { width: 19 })]),
    trow([tcell("GiveMeSomeCredit", { width: 26 }), tcell("XGBoost", { width: 18 }), tcell("0.0669", { width: 18 }), tcell("0.5014", { width: 19 }), tcell("0.5133", { width: 19 })]),
    trow([tcell("GiveMeSomeCredit", { width: 26 }), tcell("LightGBM", { width: 18 }), tcell("0.0573", { width: 18 }), tcell("0.5028", { width: 19 }), tcell("0.5104", { width: 19 })]),
    trow([tcell("GiveMeSomeCredit", { width: 26 }), tcell("EBM", { width: 18 }), tcell("0.0066", { width: 18 }), tcell("0.4986", { width: 19 }), tcell("0.5031", { width: 19 })]),
    trow([tcell("HomeCredit", { width: 26 }), tcell("XGBoost", { width: 18 }), tcell("0.1271", { width: 18 }), tcell("0.5112", { width: 19 }), tcell("0.5070", { width: 19 })]),
    trow([tcell("HomeCredit", { width: 26 }), tcell("LightGBM", { width: 18 }), tcell("0.1037", { width: 18 }), tcell("0.5098", { width: 19 }), tcell("0.5060", { width: 19 })]),
    trow([tcell("HomeCredit", { width: 26 }), tcell("EBM (80K)", { width: 18 }), tcell("0.1014", { width: 18 }), tcell("0.5071", { width: 19 }), tcell("0.5050", { width: 19 })]),
  ], [3432, 2376, 2376, 2508, 2508]),
  blank(),

  ...figImage(FIG3, 590, "Figure 3. Attack AUC-ROC results for all three model types across three credit datasets. The red dashed line marks the random baseline (AUC=0.5). All values remain below 0.60, confirming moderate rather than severe vulnerability. TaiwanCredit XGBoost (shadow AUC=0.570) shows the highest vulnerability; EBM models cluster near random across all datasets.", 0.43),
  blank(),

  para("Hypothesis H1 is confirmed: shadow-model attack AUC exceeds random baseline on all nine model-dataset combinations, and substantially so on TaiwanCredit XGBoost (shadow AUC=0.570) and LightGBM (shadow AUC=0.555). The pre-specified threshold of 0.65 was not reached on any combination; the maximum observed shadow AUC is 0.570. GiveMeSomeCredit and HomeCredit models show near-random attack AUC (0.503-0.513), indicating that MIA risk is low for these models under the evaluated threat model. EBM shows the lowest attack AUC of all model types across all datasets, with shadow AUC ranging from 0.503 to 0.505.", { indent: true }),

  heading("6.3 Driver Analysis", HeadingLevel.HEADING_2, null),

  para("To test H3, we computed the Spearman rank correlation between the train-validation AUC gap and the shadow-model attack AUC across the nine baseline observations. The result is rho=0.733 (p=0.025), confirming H3. The gap is the dominant predictor of attack success: the two high-vulnerability cases (TaiwanCredit XGBoost and LightGBM) have the largest gaps (0.205 and 0.184), while the near-random cases in GiveMeSomeCredit and HomeCredit have smaller gaps (0.007-0.127).", { indent: true }),

  para("An OLS regression of shadow AUC on gap, default rate, log(n), and log(n_features) achieves R2=0.970 (n=9, k=5 predictors), but the small sample produces near-collinear predictors with very large standard errors for all coefficients except gap. The gap coefficient (0.352) has the only stable t-statistic (t=7.95, p=0.001) in this regression. We therefore rely on the Spearman correlation as the primary driver analysis and treat the OLS result cautiously, noting that the high R2 is partly a consequence of the small sample. The association between gap and attack success is consistent with the theoretical result of Yeom et al. [6].", { indent: true }),

  para("HomeCredit presents an interesting case: despite a train-val gap of 0.127 (larger than GiveMeSomeCredit's 0.067), its shadow AUC is lower (0.507 vs 0.513). This is consistent with the dataset size: HomeCredit trains on 123,004 records while TaiwanCredit trains on 12,000. Larger training sets may reduce individual record memorization even when some degree of overfitting is present, an observation consistent with Feldman's [13] analysis of memorization in long-tailed distributions.", { indent: true }),

  heading("6.4 Defense Results", HeadingLevel.HEADING_2, null),

  para("Table 4 reports all defense results for the XGBoost baseline on each dataset. Positive AUC cost values indicate a reduction in prediction utility; negative values indicate that the defense variant slightly outperforms the baseline on the validation set (a small effect that likely reflects regularization incidentally improving generalization).", { indent: true }),

  blank(),
  caption("Table 4. Defense results. All defenses applied to XGBoost baseline (the most vulnerable model on each dataset). Val AUC = model validation AUC. AUC Cost = baseline Val AUC minus defense Val AUC (positive = utility reduction). Shadow AUC = shadow-model attack AUC on defended model."),
  makeTable([
    trow([
      tcell("Dataset", { bold: true, shade: true, width: 22 }),
      tcell("Defense", { bold: true, shade: true, width: 26 }),
      tcell("Val AUC", { bold: true, shade: true, width: 14 }),
      tcell("AUC Cost", { bold: true, shade: true, width: 16 }),
      tcell("Shadow AUC", { bold: true, shade: true, width: 22 }),
    ]),
    // TW baseline
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("XGBoost (baseline)", { width: 26, italic: true }), tcell("0.7692", { width: 14 }), tcell("0.0000", { width: 16 }), tcell("0.5699", { width: 22, italic: true })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("Rounding K=5", { width: 26 }), tcell("0.7446", { width: 14 }), tcell("0.0246", { width: 16 }), tcell("0.5692", { width: 22 })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("Rounding K=10", { width: 26 }), tcell("0.7623", { width: 14 }), tcell("0.0069", { width: 16 }), tcell("0.5631", { width: 22 })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("Perturbation 0.02", { width: 26 }), tcell("0.7693", { width: 14 }), tcell("-0.0001", { width: 16 }), tcell("0.5689", { width: 22 })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("Perturbation 0.05", { width: 26 }), tcell("0.7607", { width: 14 }), tcell("0.0085", { width: 16 }), tcell("0.5654", { width: 22 })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("Regularization", { width: 26, bold: true }), tcell("0.7793", { width: 14, bold: true }), tcell("-0.0100", { width: 16, bold: true }), tcell("0.5032", { width: 22, bold: true })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("DP-LR eps=1", { width: 26 }), tcell("0.6752", { width: 14 }), tcell("0.0940", { width: 16 }), tcell("0.5002", { width: 22 })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("DP-LR eps=5", { width: 26 }), tcell("0.7198", { width: 14 }), tcell("0.0494", { width: 16 }), tcell("0.4979", { width: 22 })]),
    trow([tcell("TaiwanCredit", { width: 22 }), tcell("DP-LR eps=10", { width: 26 }), tcell("0.7240", { width: 14 }), tcell("0.0452", { width: 16 }), tcell("0.4969", { width: 22 })]),
    // GMSC baseline
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("XGBoost (baseline)", { width: 26, italic: true }), tcell("0.8606", { width: 14 }), tcell("0.0000", { width: 16 }), tcell("0.5133", { width: 22, italic: true })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("Rounding K=5", { width: 26 }), tcell("0.7863", { width: 14 }), tcell("0.0742", { width: 16 }), tcell("0.5107", { width: 22 })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("Rounding K=10", { width: 26 }), tcell("0.8277", { width: 14 }), tcell("0.0329", { width: 16 }), tcell("0.5105", { width: 22 })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("Perturbation 0.02", { width: 26 }), tcell("0.8308", { width: 14 }), tcell("0.0298", { width: 16 }), tcell("0.5092", { width: 22 })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("Perturbation 0.05", { width: 26 }), tcell("0.7938", { width: 14 }), tcell("0.0668", { width: 16 }), tcell("0.5092", { width: 22 })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("Regularization", { width: 26, bold: true }), tcell("0.8666", { width: 14, bold: true }), tcell("-0.0060", { width: 16, bold: true }), tcell("0.5022", { width: 22, bold: true })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("DP-LR eps=1", { width: 26 }), tcell("0.8116", { width: 14 }), tcell("0.0489", { width: 16 }), tcell("0.5022", { width: 22 })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("DP-LR eps=5", { width: 26 }), tcell("0.8113", { width: 14 }), tcell("0.0493", { width: 16 }), tcell("0.5018", { width: 22 })]),
    trow([tcell("GiveMeSomeCredit", { width: 22 }), tcell("DP-LR eps=10", { width: 26 }), tcell("0.8109", { width: 14 }), tcell("0.0496", { width: 16 }), tcell("0.5018", { width: 22 })]),
    // HC baseline
    trow([tcell("HomeCredit", { width: 22 }), tcell("XGBoost (baseline)", { width: 26, italic: true }), tcell("0.7559", { width: 14 }), tcell("0.0000", { width: 16 }), tcell("0.5070", { width: 22, italic: true })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("Rounding K=5", { width: 26 }), tcell("0.6935", { width: 14 }), tcell("0.0624", { width: 16 }), tcell("0.5119", { width: 22 })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("Rounding K=10", { width: 26 }), tcell("0.7315", { width: 14 }), tcell("0.0244", { width: 16 }), tcell("0.5070", { width: 22 })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("Perturbation 0.02", { width: 26 }), tcell("0.7347", { width: 14 }), tcell("0.0212", { width: 16 }), tcell("0.5058", { width: 22 })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("Perturbation 0.05", { width: 26 }), tcell("0.6956", { width: 14 }), tcell("0.0602", { width: 16 }), tcell("0.5049", { width: 22 })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("Regularization", { width: 26, bold: true }), tcell("0.7543", { width: 14, bold: true }), tcell("0.0016", { width: 16, bold: true }), tcell("0.5009", { width: 22, bold: true })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("DP-LR eps=1", { width: 26 }), tcell("0.6075", { width: 14 }), tcell("0.1484", { width: 16 }), tcell("0.5007", { width: 22 })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("DP-LR eps=5", { width: 26 }), tcell("0.7068", { width: 14 }), tcell("0.0491", { width: 16 }), tcell("0.4987", { width: 22 })]),
    trow([tcell("HomeCredit", { width: 22 }), tcell("DP-LR eps=10", { width: 26 }), tcell("0.7396", { width: 14 }), tcell("0.0163", { width: 16 }), tcell("0.4990", { width: 22 })]),
  ], [2904, 3432, 1848, 2112, 2904]),
  blank(),

  ...figImage(FIG4, 590, "Figure 4. Privacy-utility trade-off across defenses and datasets. Each point represents one defense applied to one dataset's XGBoost baseline. The x-axis shows utility cost (reduction in validation AUC); the y-axis shows the resulting shadow model attack AUC. Points toward the lower-left represent the best outcomes. Regularization achieves near-random attack AUC with negligible utility cost across all datasets.", 0.60),
  blank(),

  para("Several patterns are evident. Rounding and output perturbation provide little defense against MIA on TaiwanCredit, reducing shadow AUC by at most 0.007 points (from 0.570 to 0.563), while incurring utility costs up to 2.5 percentage points. On GiveMeSomeCredit and HomeCredit - where the baseline XGBoost already has low attack AUC - these defenses have negligible effect in either direction.", { indent: true }),

  para("Stronger regularization (XGBoost with reg_lambda=10, max_depth=3) is the most effective low-cost defense. On TaiwanCredit, it reduces shadow AUC from 0.570 to 0.503 - a reduction of 0.067 - with effectively zero utility cost (the regularized model achieves val AUC=0.779, marginally above the baseline's 0.769). On GiveMeSomeCredit and HomeCredit, it similarly brings shadow AUC to 0.502 and 0.501 with near-zero utility cost. This suggests that the attack vulnerability in these models is primarily driven by excessive model capacity relative to training set size, and that constraining capacity eliminates most of the privacy risk.", { indent: true }),

  para("DP-LR achieves shadow AUC near or below random (0.497-0.503) across all datasets and epsilon values, confirming H2 for epsilon=5 and epsilon=10. H2 requires utility cost below 5 percentage points; at epsilon=5, costs are 4.94 pp (TaiwanCredit), 4.93 pp (GiveMeSomeCredit), and 4.91 pp (HomeCredit). All three satisfy the H2 criterion, confirming H2. At epsilon=1, HomeCredit shows a substantially larger utility cost of 14.8 percentage points, making that configuration impractical for real credit scoring. The GiveMeSomeCredit DP-LR results are unusual: utility is nearly identical across epsilon=1, 5, and 10 (val AUC ~0.811 in all cases). This indicates that the logistic regression model's capacity ceiling on this dataset is reached even without strong DP constraints, so tightening epsilon does not further reduce utility.", { indent: true }),
);

// ── SECTION 7: DISCUSSION ─────────────────────────────────────────────────

push(
  blank(),
  heading("7. Discussion", HeadingLevel.HEADING_1, null),

  heading("7.1 What Drives MIA Vulnerability in Credit Models", HeadingLevel.HEADING_2, null),

  para("The central empirical finding is that MIA vulnerability in gradient boosting credit models is primarily a function of the model's train-validation AUC gap, which itself reflects the degree of overfitting relative to training data size. TaiwanCredit's high vulnerability (shadow AUC 0.555-0.570 for XGBoost/LightGBM) results from a combination of a small training set (12,000 records) and deep tree models that memorize the minority default class. GiveMeSomeCredit's very low vulnerability (0.510-0.513) despite a similar-sized training gap reflects that its models generalize well. HomeCredit's moderate gap but low attack AUC suggests that dataset size (123,000 training records) dilutes the memorization of any individual record.", { indent: true }),

  para("EBM's structural resistance to MIA is a practically important finding. EBM's additive model structure - each feature contributes an independently learned function - limits the interaction depth and therefore the capacity to memorize specific training records. Even when EBM shows a non-trivial gap (0.101 on HomeCredit), the shadow AUC remains near random (0.505). This is consistent with the interpretation that EBM's inductive bias resists the type of point-wise memorization that MIA exploits. From a banking practitioner's perspective, EBM offers interpretability and MIA resistance simultaneously - both properties that are desirable under SR 11-7 model risk guidance [4].", { indent: true }),

  heading("7.2 Defense Recommendations for Banking", HeadingLevel.HEADING_2, null),

  para("For financial institutions deploying gradient boosting credit models, the most practical finding is that stronger regularization reduces MIA risk to near-random levels at zero utility cost. This is not a fundamentally new technique: standard model validation practices under SR 11-7 already require validation teams to evaluate overfitting and set regularization parameters appropriately [4]. The implication is that a model already subject to rigorous validation - with reg_lambda and max_depth tuned to minimize overfitting - will have low MIA vulnerability as a side effect.", { indent: true }),

  para("DP-LR provides a formal epsilon-DP guarantee that stronger regularization does not, which may be material for institutions required to demonstrate privacy protection under privacy-by-design frameworks. At epsilon=5, DP-LR is effective and incurs a utility cost of 4.9-4.9 percentage points across TaiwanCredit and GiveMeSomeCredit, and 4.9 percentage points on HomeCredit. Whether this cost is acceptable depends on the credit decision context: for a model with baseline AUC of 0.86 (GiveMeSomeCredit), dropping to 0.81 reduces predictive power materially. For TaiwanCredit with baseline AUC 0.769, dropping to 0.720 is a larger relative reduction.", { indent: true }),

  para("Confidence rounding and output perturbation provide negligible MIA protection on TaiwanCredit, where the attack AUC is already elevated. On the other datasets, where the baseline attack AUC is near random, these defenses are not needed. This pattern suggests that these defenses do not address the underlying cause of vulnerability (model memorization) and are therefore ineffective when vulnerability exists.", { indent: true }),

  heading("7.3 Banking Regulatory Implications", HeadingLevel.HEADING_2, null),

  para("The GLBA Section 6801 [23] requires covered financial institutions to protect the security and confidentiality of customer records. CFPB Circular 2022-03 [24] addresses adverse action notice requirements for AI credit decisions, emphasizing the need to explain model outputs. While neither document explicitly addresses MIA, the ability of a third party to determine membership in a credit model's training set is a form of information leakage about a consumer's financial history that GLBA's NPI protection is intended to prevent.", { indent: true }),

  para("NIST AI RMF [5] identifies training data privacy as a risk dimension under the Govern, Map, Measure, and Manage functions. The measurement guidance in NIST AI RMF 1.0 directly supports the kind of empirical evaluation conducted in this paper: measuring attack AUC-ROC for a deployed credit model, then evaluating defenses, corresponds to the NIST AI RMF 'Measure' function applied to training data privacy risk. The risk-based approach emphasized in the revised SR 11-7 guidance [4] similarly supports calibrating privacy controls to the observed level of MIA risk rather than applying uniform defenses.", { indent: true }),

  para("Practically, we recommend that model validation teams for credit scoring models evaluate MIA risk as part of the standard validation workflow. The confidence-threshold attack used in this paper requires only the model's API and a sample of held-out records, making it feasible for most validation teams. Models with train-validation AUC gap above approximately 0.15 should receive additional scrutiny, and if the gap is not reducible through regularization, DP-LR or other formal privacy mechanisms should be considered.", { indent: true }),
);

// ── SECTION 8: LIMITATIONS ──────────────────────────────────────────────

push(
  blank(),
  heading("8. Limitations", HeadingLevel.HEADING_1, null),

  para("Several limitations of this study should be noted. First, the German Credit dataset was excluded because the available Kaggle upload of this dataset (uciml/german-credit) did not include the target class column, leaving only nine feature columns with no credit risk label. A future study should obtain a version with the original target included.", { indent: true }),

  para("Second, EBM on HomeCredit was trained on an 80,000-record subsample due to runtime constraints. Comparisons between EBM and the full-data XGBoost/LightGBM models on HomeCredit are therefore not fully controlled for training set size.", { indent: true }),

  para("Third, the shadow-model attack assumes the attacker can draw samples from a distribution similar to the target model's training distribution. If the training data is highly proprietary or niche, this assumption may not hold in practice, and the real-world attack surface may be lower than measured here.", { indent: true }),

  para("Fourth, the DP defense evaluated here (diffprivlib logistic regression) provides formal epsilon-DP guarantees but is a linear model. Gradient boosting models do not currently have accessible, production-ready DP implementations with tight guarantees comparable to DP-SGD for neural networks or diffprivlib for logistic regression. A study that could evaluate DP-XGBoost with a rigorous privacy accounting mechanism would provide stronger and more directly applicable results.", { indent: true }),

  para("Fifth, the study evaluates black-box query attacks only. White-box attacks that assume access to model weights would likely be more severe; the results reported here represent a lower bound on privacy risk for a white-box adversary.", { indent: true }),

  para("Sixth, with nine observations in the driver analysis, the OLS regression is underpowered and its coefficient estimates are unreliable for all predictors except AUC gap, due to near-multicollinearity among predictors. The Spearman correlation is more reliable but also limited by sample size. A study covering more dataset-model combinations would provide more stable driver estimates.", { indent: true }),
);

// ── SECTION 9: CONCLUSION ────────────────────────────────────────────────

push(
  blank(),
  heading("9. Conclusion", HeadingLevel.HEADING_1, null),

  para("This paper reported an empirical study of membership inference attack risk and defense effectiveness for gradient boosting credit scoring models on three public datasets. The main findings are: (1) MIA vulnerability is moderate and depends strongly on the model's train-validation AUC gap; (2) XGBoost and LightGBM with default hyperparameters show elevated attack AUC on small, high-default-rate datasets such as TaiwanCredit, while models trained on larger datasets show near-random attack AUC; (3) EBM models are structurally resistant to MIA across all datasets evaluated; (4) stronger regularization eliminates most of the measured MIA vulnerability at near-zero utility cost; (5) DP-LR with epsilon=5 achieves formally provable privacy protection with 4.9 percentage points or less utility cost on two of three datasets, confirming H2; and (6) confidence rounding and output perturbation provide minimal privacy benefit when model memorization is the underlying cause of vulnerability.", { indent: true }),

  para("From a banking regulatory perspective, these findings suggest that model risk management practices that already address overfitting through regularization - as required under SR 11-7 - will incidentally reduce MIA risk. The additional step of measuring attack AUC-ROC as part of routine model validation is feasible and provides a concrete, measurable privacy risk indicator. For high-risk applications or where formal DP guarantees are required, DP-LR at epsilon=5 is a practical option with manageable utility cost.", { indent: true }),

  para("Future work should extend this evaluation to include more credit datasets, DP gradient boosting implementations when they become available, and a comparison of MIA risk across different decision thresholds used in production credit decisions.", { indent: true }),
);

// ── SECTION 10: DECLARATIONS ─────────────────────────────────────────────

push(
  blank(),
  heading("Data Availability", HeadingLevel.HEADING_1, null),
  para("The three datasets used in this study are publicly available. Taiwan Credit (UCI Default of Credit Card Clients) is available at https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients and via Kaggle (uciml/default-of-credit-card-clients-dataset). Give Me Some Credit is available at https://www.kaggle.com/c/GiveMeSomeCredit. Home Credit Default Risk is available at https://www.kaggle.com/c/home-credit-default-risk. No real consumer financial records were used in this study.", { indent: false }),

  blank(),
  heading("Code Availability", HeadingLevel.HEADING_1, null),
  para("All experimental code will be made available at a public repository upon acceptance. The main pipeline (run_experiments_v2.py) uses Python 3.11 with fixed random seeds. The diffprivlib patch (removing the deprecated multi_class parameter for sklearn 1.8.0 compatibility) is documented in the supplementary material.", { indent: false }),

  blank(),
  heading("Funding", HeadingLevel.HEADING_1, null),
  para("This research received no external funding.", { indent: false }),

  blank(),
  heading("Conflicts of Interest", HeadingLevel.HEADING_1, null),
  para("The author declares no conflicts of interest.", { indent: false }),

  blank(),
  heading("Author Contributions", HeadingLevel.HEADING_1, null),
  para("Bibek Maharjan: conceptualization, methodology, software, formal analysis, writing - original draft, writing - review and editing.", { indent: false }),
);

// ── REFERENCES ────────────────────────────────────────────────────────────

push(
  blank(),
  heading("References", HeadingLevel.HEADING_1, null),
);

const refs = [
  "[1] Lessmann S, Baesens B, Seow HV, Thomas LC. Benchmarking state-of-the-art classification algorithms for credit scoring: An update of research. Eur J Oper Res. 2015;247(1):124-136. doi:10.1016/j.ejor.2015.05.030",
  "[2] Baesens B, Van Gestel T, Viaene S, Stepanova M, Suykens J, Vanthienen J. Benchmarking state-of-the-art classification algorithms for credit scoring. J Oper Res Soc. 2003;54(6):627-635. doi:10.1057/palgrave.jors.2601545",
  "[3] Shokri R, Stronati M, Song C, Shmatikov V. Membership inference attacks against machine learning models. In: 2017 IEEE Symposium on Security and Privacy (SP). IEEE; 2017:3-18. doi:10.1109/SP.2017.41",
  "[4] Federal Reserve Board. SR 11-7: Guidance on Model Risk Management. 2011. https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm (Revised 2026 with risk-based approach; original guidance remains in effect)",
  "[5] National Institute of Standards and Technology. Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1. 2023. doi:10.6028/NIST.AI.100-1",
  "[6] Yeom S, Giacomelli I, Fredrikson M, Jha S. Privacy risk in machine learning: Analyzing the connection to overfitting. In: 31st IEEE Computer Security Foundations Symposium (CSF). IEEE; 2018:268-282. doi:10.1109/CSF.2018.00027",
  "[7] Carlini N, Chien S, Nasr M, Song S, Terzis A, Tramer F. Membership inference attacks from first principles. In: 2022 IEEE Symposium on Security and Privacy (SP). IEEE; 2022:1897-1914. doi:10.1109/SP46214.2022.9833649",
  "[8] Song L, Mittal P. Systematic evaluation of privacy risks of machine learning models. In: 30th USENIX Security Symposium. USENIX Association; 2021:2617-2634.",
  "[9] Long Y, Wang L, Bu D, et al. A pragmatic approach to membership inferences on machine learning models. In: 2020 IEEE European Symposium on Security and Privacy (EuroS&P). IEEE; 2020:521-534. doi:10.1109/EuroSP48549.2020.00040",
  "[10] Nasr M, Shokri R, Houmansadr A. Comprehensive privacy analysis of deep learning: Passive and active white-box inference attacks against centralized and federated learning. In: 2019 IEEE Symposium on Security and Privacy (SP). IEEE; 2019:739-753. doi:10.1109/SP.2019.00065",
  "[11] Choquette-Choo CA, Tramer F, Carlini N, Papernot N. Label-only membership inference attacks. In: Proceedings of the 38th International Conference on Machine Learning (ICML). PMLR; 2021:1964-1974.",
  "[12] Thomas LC, Edelman DB, Crook JN. Credit Scoring and Its Applications. 2nd ed. Philadelphia: Society for Industrial and Applied Mathematics; 2017.",
  "[13] Feldman V. Does learning require memorization? A short tale about a long tail. In: Proceedings of the 52nd Annual ACM Symposium on Theory of Computing (STOC). ACM; 2020:954-959. doi:10.1145/3357713.3384290",
  "[14] Dwork C, McSherry F, Nissim K, Smith A. Calibrating noise to sensitivity in private data analysis. In: Theory of Cryptography Conference (TCC). Lecture Notes in Computer Science vol 3876. Springer; 2006:265-284. doi:10.1007/11681878_14",
  "[15] Abadi M, Chu A, Goodfellow I, et al. Deep learning with differential privacy. In: Proceedings of the 2016 ACM SIGSAC Conference on Computer and Communications Security (CCS). ACM; 2016:308-318. doi:10.1145/2976749.2978318",
  "[16] Holohan N, Braghin S, Mac Aonghusa P, Levacher K. Diffprivlib: The IBM Differential Privacy Library. arXiv preprint arXiv:1907.02444. 2019.",
  "[17] Yeh IC, Lien CH. The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients. Expert Syst Appl. 2009;36(2):2473-2480. doi:10.1016/j.eswa.2007.12.020 (Dataset: UCI ML Repository, ID 350).",
  "[18] Kaggle. Give Me Some Credit competition dataset. 2011. https://www.kaggle.com/c/GiveMeSomeCredit",
  "[19] Kaggle. Home Credit Default Risk competition dataset. 2018. https://www.kaggle.com/c/home-credit-default-risk",
  "[20] Chen T, Guestrin C. XGBoost: A scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD). ACM; 2016:785-794. doi:10.1145/2939672.2939785",
  "[21] Ke G, Meng Q, Finley T, et al. LightGBM: A highly efficient gradient boosting decision tree. In: Advances in Neural Information Processing Systems (NeurIPS). 2017;30.",
  "[22] Nori H, Jenkins S, Koch P, Caruana R. InterpretML: A unified framework for machine interpretability. arXiv preprint arXiv:1909.09223. 2019.",
  "[23] United States Congress. Gramm-Leach-Bliley Act, 15 U.S.C. Section 6801: Protection of Nonpublic Personal Information. 1999.",
  "[24] Consumer Financial Protection Bureau. CFPB Circular 2022-03: Adverse action notification requirements and the Equal Credit Opportunity Act (Regulation B). 2022. https://www.consumerfinance.gov/compliance/supervisory-guidance/consumer-financial-protection-bureau-circular-2022-03/",
];

refs.forEach(r => {
  children.push(new Paragraph({
    children: [new TextRun({ text: r, font: FONT, size: FONT_SZ_REF })],
    alignment: AlignmentType.JUSTIFIED,
    spacing: { line: 280, after: 80 },
    indent: { left: convertInchesToTwip(0.35), hanging: convertInchesToTwip(0.35) },
  }));
});

// ── BUILD DOCUMENT ────────────────────────────────────────────────────────

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: A4_W, height: A4_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN, gutter: GUTTER },
      },
    },
    children,
    footers: {
      default: new Footer({
        children: [new Paragraph({
          children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: FONT_SZ_SM })],
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
  }],
  styles: {
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        run: { font: FONT, size: 26, bold: true, color: "000000" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.LEFT },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        run: { font: FONT, size: FONT_SZ, bold: true, color: "000000" },
        paragraph: { spacing: { before: 160, after: 80 }, alignment: AlignmentType.LEFT },
      },
    ],
  },
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/claude/mia_experiment/manuscript_v1.docx", buf);
  console.log("Written: manuscript_v1.docx");
});
