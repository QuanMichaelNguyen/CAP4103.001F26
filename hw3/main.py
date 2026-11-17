import numpy as np
import matplotlib.pyplot as plt


class Evaluator:
    """Evaluate similarity scores: accept a match when score >= threshold."""

    def __init__(self, num_thresholds, genuine_scores, impostor_scores,
                 plot_title, epsilon=1e-12):
        self.num_thresholds = num_thresholds
        self.thresholds = np.linspace(-0.1, 1.1, num_thresholds)
        self.genuine_scores = np.asarray(genuine_scores)
        self.impostor_scores = np.asarray(impostor_scores)
        self.plot_title = plot_title
        self.epsilon = epsilon

    def get_dprime(self):
        # Separation of the means divided by the pooled standard deviation.
        x = abs(np.mean(self.genuine_scores) - np.mean(self.impostor_scores))
        y = np.sqrt((np.var(self.genuine_scores) +
                     np.var(self.impostor_scores)) / 2)
        return x / (y + self.epsilon)

    def compute_rates(self):
        FPR, FNR, TPR = [], [], []
        for threshold in self.thresholds:
            TP = np.count_nonzero(self.genuine_scores >= threshold)
            FN = np.count_nonzero(self.genuine_scores < threshold)
            FP = np.count_nonzero(self.impostor_scores >= threshold)
            TN = np.count_nonzero(self.impostor_scores < threshold)
            FPR.append(FP / (FP + TN + self.epsilon))
            FNR.append(FN / (FN + TP + self.epsilon))
            TPR.append(TP / (TP + FN + self.epsilon))
        return FPR, FNR, TPR

    def get_EER(self, FPR, FNR):
        """Estimate EER at the sampled threshold with the closest error rates.

        The rates may not be exactly equal on a finite threshold grid, so
        report their average and the corresponding sampled threshold.
        """
        FPR, FNR = np.asarray(FPR), np.asarray(FNR)
        index = np.argmin(np.abs(FPR - FNR))
        EER = (FPR[index] + FNR[index]) / 2
        return EER, self.thresholds[index]

    def _format_plot(self, xlabel, ylabel, title, filename, curve=False):
        plt.xlim([-0.05, 1.05])
        if curve:
            plt.ylim([-0.05, 1.05])
        plt.grid(color='gray', linestyle='--', linewidth=0.5)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.xlabel(xlabel, fontsize=12, weight='bold')
        plt.ylabel(ylabel, fontsize=12, weight='bold')
        plt.xticks(fontsize=11)
        plt.yticks(fontsize=11)
        plt.title(title, fontsize=15, weight='bold')
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()

    def plot_score_distribution(self):
        plt.figure(figsize=(6.4, 4.8))
        # Identical bins make the two histograms directly comparable.
        bins = np.linspace(0, 1, 41)
        plt.hist(self.genuine_scores, bins=bins, color='green', lw=1.5,
                 histtype='step', hatch='//', label='Genuine')
        plt.hist(self.impostor_scores, bins=bins, color='red', lw=1.5,
                 histtype='step', hatch='\\\\', label='Impostor')
        plt.legend(loc='upper left', fontsize=11)
        self._format_plot(
            'Similarity score', 'Number of scores',
            'Score Distribution Plot\nd-prime = %.2f\nSystem %s' %
            (self.get_dprime(), self.plot_title),
            'score_distribution_plot_(%s).png' % self.plot_title)

    def plot_det_curve(self, FPR, FNR):
        EER, EER_threshold = self.get_EER(FPR, FNR)
        plt.figure(figsize=(6.4, 4.8))
        plt.plot(FPR, FNR, lw=2, color='blue')
        # The y=x line identifies equal FPR and FNR; it is not a random
        # classifier's DET curve (that would be y=1-x).
        plt.plot([0, 1], [0, 1], '--', lw=0.5, color='black')
        plt.scatter([EER], [EER], c='black', s=60)
        plt.text(EER + 0.05, EER + 0.05, 'EER', fontsize=11)
        self._format_plot(
            'False Pos. Rate', 'False Neg. Rate',
            'Detection Error Tradeoff Curve\nEER = %.5f at t = %.3f\nSystem %s' %
            (EER, EER_threshold, self.plot_title),
            'det_curve_(%s).png' % self.plot_title, curve=True)

    def plot_roc_curve(self, FPR, TPR):
        plt.figure(figsize=(6.4, 4.8))
        plt.plot(FPR, TPR, lw=2, color='blue')
        plt.plot([0, 1], [0, 1], '--', lw=0.5, color='black')
        self._format_plot(
            'False Pos. Rate', 'True Pos. Rate',
            'Receiver Operating Characteristic Curve\nSystem %s' % self.plot_title,
            'roc_curve_(%s).png' % self.plot_title, curve=True)


def main():
    seed = 42
    rng = np.random.default_rng(seed)
    print('Random seed:', seed)
    systems = ['A', 'B', 'C']

    for system in systems:
        # Keep the starter code's random generation and draw order.
        gSize = rng.integers(5000, 10000)
        iSize = rng.integers(15000, 20000)
        gDists = rng.integers(1, 10)
        iDists = rng.integers(1, 10)

        genuine_scores = []
        for gDist in range(gDists):
            size = int(gSize / gDists)
            loc = (1.00 - 0.4) * rng.random() + 0.4
            scale = (0.3 - 0.05) * rng.random() + 0.05
            g_scores = np.clip(rng.normal(loc=loc, scale=scale, size=size), 0, 1)
            genuine_scores = np.concatenate([genuine_scores, g_scores])

        impostor_scores = []
        for iDist in range(iDists):
            size = int(iSize / iDists)
            loc = (0.6 - 0.0) * rng.random() + 0.0
            scale = (0.3 - 0.05) * rng.random() + 0.05
            i_scores = np.clip(rng.normal(loc=loc, scale=scale, size=size), 0, 1)
            impostor_scores = np.concatenate([impostor_scores, i_scores])

        evaluator = Evaluator(
            epsilon=1e-12, num_thresholds=500,
            genuine_scores=genuine_scores, impostor_scores=impostor_scores,
            plot_title=system)
        FPR, FNR, TPR = evaluator.compute_rates()
        EER, threshold = evaluator.get_EER(FPR, FNR)
        print('System %s: d-prime=%.5f, EER=%.5f, threshold=%.5f' %
              (system, evaluator.get_dprime(), EER, threshold))
        evaluator.plot_score_distribution()
        evaluator.plot_det_curve(FPR, FNR)
        evaluator.plot_roc_curve(FPR, TPR)


if __name__ == '__main__':
    main()
