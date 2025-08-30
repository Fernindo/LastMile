#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>

namespace py = pybind11;

struct InputRow {
    std::string produkt;
    std::string jednotky;
    int pocet_materialu;
    double koeficient_material;
    double nakup_materialu;
    int pocet_prace;
    double koeficient_prace;
    double cena_prace;
    bool sync;
};

struct Change {
    std::string section;
    std::string product;
    std::string field;
    std::string old_value;
    std::string new_value;
};

class UndoEngine {
    std::vector<Change> undo_stack_;
    std::vector<Change> redo_stack_;
public:
    void apply(const Change& ch) {
        undo_stack_.push_back(ch);
        redo_stack_.clear();
    }
    py::object undo() {
        if (undo_stack_.empty()) {
            return py::none();
        }
        Change ch = undo_stack_.back();
        undo_stack_.pop_back();
        redo_stack_.push_back(ch);
        return py::cast(ch);
    }
    py::object redo() {
        if (redo_stack_.empty()) {
            return py::none();
        }
        Change ch = redo_stack_.back();
        redo_stack_.pop_back();
        undo_stack_.push_back(ch);
        return py::cast(ch);
    }
    void clear() {
        undo_stack_.clear();
        redo_stack_.clear();
    }
};

static std::string fmt(double value) {
    std::ostringstream oss;
    oss.setf(std::ios::fixed);
    oss << std::setprecision(2) << value;
    return oss.str();
}

py::tuple compute_rows_and_totals(const std::vector<InputRow>& rows) {
    py::list out_rows;
    double total_material = 0.0;
    double total_work = 0.0;
    for (const auto& r : rows) {
        int poc_mat = r.pocet_materialu;
        double koef_mat = r.koeficient_material;
        double nakup_mat = r.nakup_materialu;
        double predaj_mat_jedn = nakup_mat * koef_mat;
        double predaj_mat_spolu = predaj_mat_jedn * poc_mat;
        double nakup_mat_spolu = nakup_mat * poc_mat;
        double zisk_mat = predaj_mat_spolu - nakup_mat_spolu;
        double marza_mat = predaj_mat_spolu != 0.0 ? (zisk_mat / predaj_mat_spolu * 100.0) : 0.0;

        int poc_pr = r.pocet_prace;
        double koef_pr = r.koeficient_prace;
        double cena_pr = r.cena_prace;
        double predaj_praca_jedn = cena_pr * koef_pr;
        double predaj_praca_spolu = predaj_praca_jedn * poc_pr;
        double nakup_praca_spolu = cena_pr * poc_pr;
        double zisk_pr = predaj_praca_spolu - nakup_praca_spolu;
        double marza_pr = predaj_praca_spolu != 0.0 ? (zisk_pr / predaj_praca_spolu * 100.0) : 0.0;
        double predaj_spolu = predaj_mat_spolu + predaj_praca_spolu;

        total_material += predaj_mat_spolu;
        total_work += predaj_praca_spolu;

        py::tuple row_out = py::make_tuple(
            r.produkt,
            r.jednotky,
            std::to_string(poc_mat),
            fmt(koef_mat),
            fmt(nakup_mat),
            fmt(predaj_mat_jedn),
            fmt(nakup_mat_spolu),
            fmt(predaj_mat_spolu),
            fmt(zisk_mat),
            fmt(marza_mat),
            std::to_string(poc_pr),
            fmt(koef_pr),
            fmt(cena_pr),
            fmt(nakup_praca_spolu),
            fmt(predaj_praca_jedn),
            fmt(predaj_praca_spolu),
            fmt(zisk_pr),
            fmt(marza_pr),
            fmt(predaj_spolu),
            r.sync ? std::string("\u2713") : std::string("")
        );
        out_rows.append(row_out);
    }
    return py::make_tuple(out_rows, total_material, total_work);
}

py::list parse_rows(const py::sequence& block) {
    py::list result;
    for (auto item : block) {
        auto seq = py::cast<py::sequence>(item);
        if (py::len(seq) < 20) {
            continue;
        }
        InputRow r;
        r.produkt = py::cast<std::string>(seq[0]);
        r.jednotky = py::cast<std::string>(seq[1]);
        r.pocet_materialu = std::stoi(py::cast<std::string>(seq[2]));
        r.koeficient_material = std::stod(py::cast<std::string>(seq[3]));
        r.nakup_materialu = std::stod(py::cast<std::string>(seq[4]));
        r.pocet_prace = std::stoi(py::cast<std::string>(seq[10]));
        r.koeficient_prace = std::stod(py::cast<std::string>(seq[11]));
        r.cena_prace = std::stod(py::cast<std::string>(seq[12]));
        r.sync = py::cast<std::string>(seq[19]) == "\u2713";
        result.append(py::cast(r));
    }
    return result;
}

PYBIND11_MODULE(fastbasket, m) {
    py::class_<InputRow>(m, "InputRow")
        .def(py::init<const std::string&, const std::string&, int, double, double, int, double, double, bool>(),
             py::arg("produkt"), py::arg("jednotky"), py::arg("pocet_materialu"), py::arg("koeficient_material"),
             py::arg("nakup_materialu"), py::arg("pocet_prace"), py::arg("koeficient_prace"),
             py::arg("cena_prace"), py::arg("sync"))
        .def_readwrite("produkt", &InputRow::produkt)
        .def_readwrite("jednotky", &InputRow::jednotky)
        .def_readwrite("pocet_materialu", &InputRow::pocet_materialu)
        .def_readwrite("koeficient_material", &InputRow::koeficient_material)
        .def_readwrite("nakup_materialu", &InputRow::nakup_materialu)
        .def_readwrite("pocet_prace", &InputRow::pocet_prace)
        .def_readwrite("koeficient_prace", &InputRow::koeficient_prace)
        .def_readwrite("cena_prace", &InputRow::cena_prace)
        .def_readwrite("sync", &InputRow::sync);

    py::class_<Change>(m, "Change")
        .def(py::init<const std::string&, const std::string&, const std::string&, const std::string&, const std::string&>(),
             py::arg("section"), py::arg("product"), py::arg("field"), py::arg("old_value"), py::arg("new_value"))
        .def_readwrite("section", &Change::section)
        .def_readwrite("product", &Change::product)
        .def_readwrite("field", &Change::field)
        .def_readwrite("old_value", &Change::old_value)
        .def_readwrite("new_value", &Change::new_value);

    py::class_<UndoEngine>(m, "UndoEngine")
        .def(py::init<>())
        .def("apply", &UndoEngine::apply)
        .def("undo", &UndoEngine::undo)
        .def("redo", &UndoEngine::redo)
        .def("clear", &UndoEngine::clear);

    m.def("compute_rows_and_totals", &compute_rows_and_totals, py::arg("rows"));
    m.def("parse_rows", &parse_rows, py::arg("block"));
}

