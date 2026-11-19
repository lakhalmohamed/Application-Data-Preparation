import React, { useState, useEffect, useMemo } from 'react';
import { useData } from '../context/DataContext';
import { Settings, Calendar, Calculator, FileText, CheckCircle2, Sparkles, Layers } from 'lucide-react';

const DATE_KEYWORDS = ['date', 'time', 'timestamp', 'annee', 'year', 'mois', 'month', 'jour', 'day', 'created', 'updated', 'birth', 'naissance', 'dt', 'debut', 'fin', 'period'];

const TransformsPage = () => {
  const { 
    metadata, 
    analysisResults, 
    loading, 
    extractDatetimeFeatures, 
    createNumericInteraction, 
    binNumericColumn, 
    extractTextFeatures,
    cleaningHistory 
  } = useData();

  const [activeTab, setActiveTab] = useState('datetime');

  // Datetime state
  const [selectedDateCol, setSelectedDateCol] = useState('');
  const [showAllColsForDate, setShowAllColsForDate] = useState(false);
  const [dateOptions, setDateOptions] = useState({
    extractYear: true,
    extractMonth: true,
    extractDay: true,
    extractDayOfWeek: true,
    extractIsWeekend: true,
    extractQuarter: true,
    extractHour: false,
    referenceDate: '',
  });

  // Numeric interaction state
  const [numColA, setNumColA] = useState('');
  const [numColB, setNumColB] = useState('');
  const [numOp, setNumOp] = useState('multiply');
  const [numOutputName, setNumOutputName] = useState('');

  // Binning state
  const [binCol, setBinCol] = useState('');
  const [binCount, setBinCount] = useState(5);
  const [binStrategy, setBinStrategy] = useState('quantile');
  const [binOutputName, setBinOutputName] = useState('');

  // Text state
  const [textCol, setTextCol] = useState('');
  const [extractCharLength, setExtractCharLength] = useState(true);
  const [extractWordCount, setExtractWordCount] = useState(true);

  // Column categorization
  const { datetimeColumns, numericColumns, textColumns } = useMemo(() => {
    const allCols = metadata?.columns || [];
    const profiles = analysisResults?.profiles || {};

    const dt = allCols.filter((col) => {
      const prof = profiles[col];
      if (prof) {
        const dtype = (prof.detected_type || '').toLowerCase();
        const pdType = (prof.pandas_dtype || '').toLowerCase();
        if (dtype.includes('temporel') || dtype.includes('date') || pdType.includes('date') || pdType.includes('time')) {
          return true;
        }
      }
      return DATE_KEYWORDS.some((kw) => col.toLowerCase().includes(kw));
    });

    const num = allCols.filter((col) => {
      const prof = profiles[col];
      if (prof) {
        const dtype = (prof.detected_type || '').toLowerCase();
        const pdType = (prof.pandas_dtype || '').toLowerCase();
        if (dtype.includes('numérique') || dtype.includes('numerique') || pdType.includes('int') || pdType.includes('float')) {
          return true;
        }
      }
      const dtype = (metadata?.dtypes?.[col] || '').toLowerCase();
      return dtype.includes('int') || dtype.includes('float');
    });

    const txt = allCols.filter((col) => !dt.includes(col) && !num.includes(col));

    return {
      datetimeColumns: dt,
      numericColumns: num.length > 0 ? num : allCols,
      textColumns: txt.length > 0 ? txt : allCols,
    };
  }, [metadata, analysisResults]);

  // Set default selections
  useEffect(() => {
    if (datetimeColumns.length > 0 && !selectedDateCol) {
      setSelectedDateCol(datetimeColumns[0]);
    } else if (metadata?.columns?.length > 0 && !selectedDateCol) {
      setSelectedDateCol(metadata.columns[0]);
    }

    if (numericColumns.length > 0) {
      if (!numColA) setNumColA(numericColumns[0]);
      if (!numColB) setNumColB(numericColumns[1] || numericColumns[0]);
      if (!binCol) setBinCol(numericColumns[0]);
    }

    if (textColumns.length > 0 && !textCol) {
      setTextCol(textColumns[0]);
    }
  }, [datetimeColumns, numericColumns, textColumns, metadata]);

  if (!metadata) {
    return (
      <div className="p-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
          <Settings className="w-12 h-12 mx-auto mb-4 text-yellow-600" />
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            Aucun dataset chargé
          </h3>
          <p className="text-yellow-700">
            Chargez un dataset depuis la page Import pour accéder aux transformations.
          </p>
        </div>
      </div>
    );
  }

  const handleDatetimeExtract = async () => {
    if (!selectedDateCol) return;
    try {
      await extractDatetimeFeatures(selectedDateCol, dateOptions);
    } catch (err) {
      console.error('Date extraction failed:', err);
    }
  };

  const handleNumericInteraction = async () => {
    if (!numColA || !numColB) return;
    try {
      await createNumericInteraction(numColA, numColB, numOp, numOutputName || null);
      setNumOutputName('');
    } catch (err) {
      console.error('Numeric interaction failed:', err);
    }
  };

  const handleBinning = async () => {
    if (!binCol) return;
    try {
      await binNumericColumn(binCol, Number(binCount), binStrategy, binOutputName || null);
      setBinOutputName('');
    } catch (err) {
      console.error('Binning failed:', err);
    }
  };

  const handleTextExtract = async () => {
    if (!textCol) return;
    try {
      await extractTextFeatures(textCol, {
        extractCharLength,
        extractWordCount,
      });
    } catch (err) {
      console.error('Text extraction failed:', err);
    }
  };

  const availableDateCols = showAllColsForDate ? metadata.columns : (datetimeColumns.length > 0 ? datetimeColumns : metadata.columns);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Transformations & Feature Engineering</h1>
        <p className="text-gray-600">Décomposition temporelle, interactions numériques et traitement textuel</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Transformation Controls */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="border-b border-gray-200 bg-gray-50/50">
              <nav className="flex">
                <button
                  onClick={() => setActiveTab('datetime')}
                  className={`px-6 py-4 font-medium transition-colors flex items-center gap-2 ${
                    activeTab === 'datetime'
                      ? 'border-b-2 border-primary text-primary bg-white'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Calendar className="w-4 h-4" />
                  Temporel (Dates)
                </button>
                <button
                  onClick={() => setActiveTab('numeric')}
                  className={`px-6 py-4 font-medium transition-colors flex items-center gap-2 ${
                    activeTab === 'numeric'
                      ? 'border-b-2 border-primary text-primary bg-white'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Calculator className="w-4 h-4" />
                  Numérique
                </button>
                <button
                  onClick={() => setActiveTab('text')}
                  className={`px-6 py-4 font-medium transition-colors flex items-center gap-2 ${
                    activeTab === 'text'
                      ? 'border-b-2 border-primary text-primary bg-white'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  Textuel
                </button>
              </nav>
            </div>

            <div className="p-6">
              {/* TAB 1: DATETIME */}
              {activeTab === 'datetime' && (
                <div className="space-y-6">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="block text-sm font-medium text-gray-700">
                        Colonne de date / horodatage
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowAllColsForDate(!showAllColsForDate)}
                        className="text-xs text-primary hover:underline"
                      >
                        {showAllColsForDate ? 'Afficher uniquement les dates détectées' : 'Afficher toutes les colonnes'}
                      </button>
                    </div>

                    <select
                      value={selectedDateCol}
                      onChange={(e) => setSelectedDateCol(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    >
                      {availableDateCols.map((col) => {
                        const isDetected = datetimeColumns.includes(col);
                        return (
                          <option key={col} value={col}>
                            {col} {isDetected ? '✓ (Date détectée)' : ''}
                          </option>
                        );
                      })}
                    </select>

                    {datetimeColumns.length > 0 && !showAllColsForDate && (
                      <p className="text-xs text-green-700 mt-1 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        {datetimeColumns.length} colonne(s) temporelle(s) détectée(s) automatiquement : {datetimeColumns.join(', ')}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Caractéristiques à dériver :
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractYear}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractYear: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Année</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractMonth}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractMonth: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Mois</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractDay}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractDay: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Jour</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractDayOfWeek}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractDayOfWeek: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Jour semaine</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractIsWeekend}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractIsWeekend: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Est Week-end</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractQuarter}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractQuarter: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Trimestre</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={dateOptions.extractHour}
                          onChange={(e) => setDateOptions({ ...dateOptions, extractHour: e.target.checked })}
                          className="rounded text-primary focus:ring-primary"
                        />
                        <span className="text-sm font-medium text-gray-800">Heure (si présente)</span>
                      </label>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Date de référence (Optionnel, calcul d'ancienneté en jours)
                    </label>
                    <input
                      type="date"
                      value={dateOptions.referenceDate}
                      onChange={(e) => setDateOptions({ ...dateOptions, referenceDate: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>

                  <button
                    onClick={handleDatetimeExtract}
                    disabled={loading || !selectedDateCol}
                    className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2 shadow-sm"
                  >
                    <Sparkles className="w-5 h-5" />
                    {loading ? 'Extraction en cours...' : 'Extraire les caractéristiques temporelles'}
                  </button>
                </div>
              )}

              {/* TAB 2: NUMERIC */}
              {activeTab === 'numeric' && (
                <div className="space-y-8">
                  {/* Sub-section: Interactions */}
                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900 border-b pb-2 flex items-center gap-2">
                      <Calculator className="w-4 h-4 text-primary" />
                      Interaction entre deux variables numériques
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Variable A</label>
                        <select
                          value={numColA}
                          onChange={(e) => setNumColA(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          {numericColumns.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Variable B</label>
                        <select
                          value={numColB}
                          onChange={(e) => setNumColB(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          {numericColumns.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Opération</label>
                        <select
                          value={numOp}
                          onChange={(e) => setNumOp(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          <option value="multiply">Multiplication (A × B)</option>
                          <option value="ratio">Ratio / Division (A ÷ B)</option>
                          <option value="sum">Addition (A + B)</option>
                          <option value="diff">Différence (A - B)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nom personnalisé (optionnel)</label>
                        <input
                          type="text"
                          placeholder="ex: ratio_salaire_age"
                          value={numOutputName}
                          onChange={(e) => setNumOutputName(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        />
                      </div>
                    </div>

                    <button
                      onClick={handleNumericInteraction}
                      disabled={loading || !numColA || !numColB}
                      className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      {loading ? 'Calcul en cours...' : "Créer l'interaction numérique"}
                    </button>
                  </div>

                  {/* Sub-section: Binning */}
                  <div className="space-y-4 pt-4 border-t border-gray-200">
                    <h3 className="font-semibold text-gray-900 border-b pb-2 flex items-center gap-2">
                      <Layers className="w-4 h-4 text-primary" />
                      Discrétisation (Binning)
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Colonne</label>
                        <select
                          value={binCol}
                          onChange={(e) => setBinCol(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          {numericColumns.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de tranches</label>
                        <input
                          type="number"
                          min="2"
                          max="20"
                          value={binCount}
                          onChange={(e) => setBinCount(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Méthode</label>
                        <select
                          value={binStrategy}
                          onChange={(e) => setBinStrategy(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                        >
                          <option value="quantile">Quantiles (effectifs égaux)</option>
                          <option value="uniform">Uniforme (intervalles égaux)</option>
                        </select>
                      </div>
                    </div>

                    <button
                      onClick={handleBinning}
                      disabled={loading || !binCol}
                      className="w-full px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      {loading ? 'Discrétisation...' : 'Discrétiser la colonne'}
                    </button>
                  </div>
                </div>
              )}

              {/* TAB 3: TEXT */}
              {activeTab === 'text' && (
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Colonne textuelle
                    </label>
                    <select
                      value={textCol}
                      onChange={(e) => setTextCol(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      {textColumns.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={extractCharLength}
                        onChange={(e) => setExtractCharLength(e.target.checked)}
                        className="rounded text-primary focus:ring-primary"
                      />
                      <span className="text-sm font-medium text-gray-800">Longueur en caractères (nb_caracteres)</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={extractWordCount}
                        onChange={(e) => setExtractWordCount(e.target.checked)}
                        className="rounded text-primary focus:ring-primary"
                      />
                      <span className="text-sm font-medium text-gray-800">Nombre de mots (nb_mots)</span>
                    </label>
                  </div>

                  <button
                    onClick={handleTextExtract}
                    disabled={loading || !textCol}
                    className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-blue-700 font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    <FileText className="w-5 h-5" />
                    {loading ? 'Extraction...' : 'Extraire les caractéristiques textuelles'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Operations History & Current Columns */}
        <div className="space-y-6">
          <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900">
              <Sparkles className="w-5 h-5 text-primary" />
              Journal des transformations
            </h2>
            {cleaningHistory.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-6">
                Aucune transformation effectuée pour le moment.
              </p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {cleaningHistory.map((op, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-gray-900">{op.operation}</span>
                      <span className="text-gray-400 text-[10px]">{op.timestamp}</span>
                    </div>
                    <p className="text-gray-600 font-medium">Colonne : {op.column}</p>
                    <p className="text-gray-500 mt-1">{op.details}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-card rounded-lg border border-gray-200 p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Colonnes actuelles ({metadata.columns.length})</h3>
            <div className="max-h-48 overflow-y-auto flex flex-wrap gap-1.5">
              {metadata.columns.map((c) => (
                <span key={c} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs border border-gray-200">
                  {c}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransformsPage;
