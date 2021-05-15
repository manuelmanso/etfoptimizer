import Typography from "@material-ui/core/Typography";
import Paper from "@material-ui/core/Paper";
import Search from "./Search";

function App() {
    return (
        <div className="App" style={{}}>
            <Paper
                elevation={10}
                variant="outlined"
                style={{
                    backgroundColor: "darkgray",
                    margin: "25px",
                }}
            >
                <Typography variant="h4" component="h2" gutterBottom style={{ margin: "15px" }}>
                    ETF Optimizer
                </Typography>
                <Typography variant="h6" component="h2" style={{ marginLeft: "15px" }}>
                    Optimize an ETF portfolio by defining your own filters. Using ETFs from justETF and historical data from Refinitiv
                    Eikon.
                </Typography>
            </Paper>
            <Paper
                elevation={10}
                variant="outlined"
                style={{
                    backgroundColor: "darkgray",
                    margin: "100px",
                    marginTop: "0px",
                }}
            >
                <Search />
            </Paper>
        </div>
    );
}

export default App;
